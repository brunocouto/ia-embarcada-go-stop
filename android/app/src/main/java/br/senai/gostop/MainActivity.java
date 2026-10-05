package br.senai.gostop;

import android.Manifest;
import android.app.Activity;
import android.content.pm.ApplicationInfo;
import android.content.pm.PackageManager;
import android.graphics.Typeface;
import android.media.AudioFormat;
import android.media.AudioRecord;
import android.media.MediaRecorder;
import android.os.Bundle;
import android.os.SystemClock;
import android.util.Log;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

import org.json.JSONArray;
import org.json.JSONObject;
import org.tensorflow.lite.DataType;
import org.tensorflow.lite.Interpreter;

import java.io.ByteArrayOutputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.Locale;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/** Demonstra a pipeline microfone -> áudio normalizado -> LiteRT -> resultado. */
public final class MainActivity extends Activity {
    private static final int RECORD_PERMISSION_REQUEST = 10;
    private static final int SAMPLE_RATE = 16_000;
    private static final int SAMPLES_PER_CLIP = 16_000;

    private final ExecutorService worker = Executors.newSingleThreadExecutor();
    private Interpreter interpreter;
    private String[] labels;
    private Button recordButton;
    private TextView statusView;
    private TextView resultView;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        LinearLayout page = new LinearLayout(this);
        page.setOrientation(LinearLayout.VERTICAL);
        page.setPadding(dp(24), dp(36), dp(24), dp(24));
        page.setGravity(Gravity.TOP | Gravity.CENTER_HORIZONTAL);
        page.setFitsSystemWindows(true);

        TextView title = new TextView(this);
        title.setText("Reconhecer GO ou STOP");
        title.setTextSize(24);
        title.setTypeface(null, Typeface.BOLD);
        page.addView(title, fullWidth());

        TextView instruction = new TextView(this);
        instruction.setText("Toque no botão e diga uma palavra em inglês: go ou stop. A gravação dura 1 segundo.");
        instruction.setTextSize(16);
        instruction.setPadding(0, dp(16), 0, dp(20));
        page.addView(instruction, fullWidth());

        recordButton = new Button(this);
        recordButton.setText("Gravar e classificar");
        recordButton.setOnClickListener(view -> requestRecordOrStart());
        page.addView(recordButton, fullWidth());

        statusView = new TextView(this);
        statusView.setText("Pronto para gravar.");
        statusView.setTextSize(16);
        statusView.setPadding(0, dp(24), 0, dp(12));
        page.addView(statusView, fullWidth());

        resultView = new TextView(this);
        resultView.setText("Resultado: —");
        resultView.setTextSize(21);
        resultView.setTypeface(null, Typeface.BOLD);
        page.addView(resultView, fullWidth());

        setContentView(page);

        String debugSample = getIntent().getStringExtra("debug_sample");
        if ((getApplicationInfo().flags & ApplicationInfo.FLAG_DEBUGGABLE) != 0
                && ("go".equals(debugSample) || "stop".equals(debugSample))) {
            recordButton.setEnabled(false);
            statusView.setText("Testando amostra do dataset no Android virtual (sem microfone)...");
            worker.execute(() -> classifyDebugSample(debugSample));
        }
    }

    private LinearLayout.LayoutParams fullWidth() {
        return new LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.MATCH_PARENT,
            LinearLayout.LayoutParams.WRAP_CONTENT
        );
    }

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }

    private void requestRecordOrStart() {
        if (checkSelfPermission(Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{Manifest.permission.RECORD_AUDIO}, RECORD_PERMISSION_REQUEST);
            return;
        }
        recordButton.setEnabled(false);
        resultView.setText("Resultado: —");
        statusView.setText("Preparando gravação...");
        worker.execute(this::captureAndClassify);
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode != RECORD_PERMISSION_REQUEST) {
            return;
        }
        if (grantResults.length > 0 && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
            statusView.setText("Permissão concedida. Toque no botão novamente e fale após o início da gravação.");
        } else {
            statusView.setText("Permissão do microfone negada. É necessária para a demonstração.");
        }
    }

    private void captureAndClassify() {
        AudioRecord recorder = null;
        try {
            ensureModelLoaded();
            int minimumBytes = AudioRecord.getMinBufferSize(
                SAMPLE_RATE, AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT
            );
            if (minimumBytes <= 0) {
                throw new IllegalStateException("O dispositivo não aceita áudio mono PCM16 a 16 kHz.");
            }
            recorder = new AudioRecord(
                MediaRecorder.AudioSource.VOICE_RECOGNITION,
                SAMPLE_RATE,
                AudioFormat.CHANNEL_IN_MONO,
                AudioFormat.ENCODING_PCM_16BIT,
                Math.max(minimumBytes, SAMPLES_PER_CLIP * 2)
            );
            if (recorder.getState() != AudioRecord.STATE_INITIALIZED) {
                throw new IllegalStateException("Não foi possível iniciar o microfone.");
            }

            short[] pcm = new short[SAMPLES_PER_CLIP];
            recorder.startRecording();
            showStatus("Gravando 1 segundo: fale GO ou STOP agora.");
            int offset = 0;
            while (offset < pcm.length) {
                int count = recorder.read(pcm, offset, pcm.length - offset, AudioRecord.READ_BLOCKING);
                if (count <= 0) {
                    throw new IllegalStateException("Falha ao ler o microfone (código " + count + ").");
                }
                offset += count;
            }
            recorder.stop();
            saveDebugCapture(pcm);
            classify(pcm, "Captura e inferência concluídas no dispositivo.");
        } catch (Exception error) {
            showError(error.getMessage() == null ? error.getClass().getSimpleName() : error.getMessage());
        } finally {
            if (recorder != null) {
                if (recorder.getRecordingState() == AudioRecord.RECORDSTATE_RECORDING) {
                    recorder.stop();
                }
                recorder.release();
            }
            runOnUiThread(() -> {
                if (!isDestroyed()) {
                    recordButton.setEnabled(true);
                }
            });
        }
    }

    private void saveDebugCapture(short[] pcm) {
        if ((getApplicationInfo().flags & ApplicationInfo.FLAG_DEBUGGABLE) == 0) {
            return;
        }
        ByteBuffer buffer = ByteBuffer.allocate(pcm.length * 2).order(ByteOrder.LITTLE_ENDIAN);
        int peak = 0;
        for (short sample : pcm) {
            buffer.putShort(sample);
            peak = Math.max(peak, Math.abs((int) sample));
        }
        try (FileOutputStream output = openFileOutput("last_capture.pcm", MODE_PRIVATE)) {
            output.write(buffer.array());
            Log.i("GoStopCapture", "samples=" + pcm.length + "; peak_pcm16=" + peak);
        } catch (IOException error) {
            Log.w("GoStopCapture", "Não foi possível guardar a captura de teste.", error);
        }
    }

    private void classifyDebugSample(String label) {
        try {
            ensureModelLoaded();
            byte[] raw = readAsset("sample_" + label + ".pcm");
            if (raw.length != SAMPLES_PER_CLIP * 2) {
                throw new IllegalStateException("Amostra de teste com tamanho inválido.");
            }
            short[] pcm = new short[SAMPLES_PER_CLIP];
            ByteBuffer buffer = ByteBuffer.wrap(raw).order(ByteOrder.LITTLE_ENDIAN);
            for (int index = 0; index < SAMPLES_PER_CLIP; index++) {
                pcm[index] = buffer.getShort();
            }
            classify(pcm, "Teste com amostra " + label.toUpperCase(Locale.ROOT) + " do dataset (sem microfone).");
        } catch (Exception error) {
            showError(error.getMessage() == null ? error.getClass().getSimpleName() : error.getMessage());
        } finally {
            runOnUiThread(() -> {
                if (!isDestroyed()) {
                    recordButton.setEnabled(true);
                }
            });
        }
    }

    private void classify(short[] pcm, String completionStatus) {
        float[][][] input = new float[1][SAMPLES_PER_CLIP][1];
        for (int index = 0; index < SAMPLES_PER_CLIP; index++) {
            input[0][index][0] = pcm[index] / 32768.0f;
        }
        float[][] output = new float[1][labels.length];
        showStatus("Executando inferência no Android...");
        long startNanos = SystemClock.elapsedRealtimeNanos();
        interpreter.run(input, output);
        double inferenceMs = (SystemClock.elapsedRealtimeNanos() - startNanos) / 1_000_000.0;

        int selected = output[0][0] >= output[0][1] ? 0 : 1;
        String result = String.format(
            Locale.getDefault(),
            "Resultado: %s (pontuação %.1f%%)\nInferência: %.1f ms",
            labels[selected].toUpperCase(Locale.ROOT), output[0][selected] * 100.0f, inferenceMs
        );
        showResult(result, completionStatus);
    }

    private void ensureModelLoaded() throws Exception {
        if (interpreter != null) {
            return;
        }
        byte[] bytes = readAsset("go_stop_quantized.tflite");
        ByteBuffer modelBuffer = ByteBuffer.allocateDirect(bytes.length).order(ByteOrder.nativeOrder());
        modelBuffer.put(bytes);
        modelBuffer.rewind();
        Interpreter loadedModel = new Interpreter(modelBuffer, new Interpreter.Options().setNumThreads(2));
        try {
            JSONObject labelFile = new JSONObject(
                new String(readAsset("labels.json"), StandardCharsets.UTF_8)
            );
            JSONArray labelArray = labelFile.getJSONArray("labels_in_order");
            if (labelArray.length() != 2) {
                throw new IllegalStateException("Esperados dois rótulos no modelo.");
            }
            String[] loadedLabels = new String[]{labelArray.getString(0), labelArray.getString(1)};
            if (!Arrays.equals(loadedModel.getInputTensor(0).shape(), new int[]{1, SAMPLES_PER_CLIP, 1})
                    || loadedModel.getInputTensor(0).dataType() != DataType.FLOAT32
                    || !Arrays.equals(loadedModel.getOutputTensor(0).shape(), new int[]{1, 2})
                    || loadedModel.getOutputTensor(0).dataType() != DataType.FLOAT32) {
                throw new IllegalStateException("Formato do modelo diferente do treinamento.");
            }
            labels = loadedLabels;
            interpreter = loadedModel;
        } catch (Exception error) {
            loadedModel.close();
            throw error;
        }
    }

    private byte[] readAsset(String filename) throws Exception {
        try (InputStream input = getAssets().open(filename);
             ByteArrayOutputStream output = new ByteArrayOutputStream()) {
            byte[] chunk = new byte[8192];
            int count;
            while ((count = input.read(chunk)) != -1) {
                output.write(chunk, 0, count);
            }
            return output.toByteArray();
        }
    }

    private void showStatus(String message) {
        runOnUiThread(() -> {
            if (!isDestroyed()) {
                statusView.setText(message);
            }
        });
    }

    private void showResult(String message, String completionStatus) {
        runOnUiThread(() -> {
            if (!isDestroyed()) {
                statusView.setText(completionStatus);
                resultView.setText(message);
            }
        });
    }

    private void showError(String message) {
        runOnUiThread(() -> {
            if (!isDestroyed()) {
                statusView.setText("Erro: " + message);
            }
        });
    }

    @Override
    protected void onDestroy() {
        worker.execute(() -> {
            if (interpreter != null) {
                interpreter.close();
            }
        });
        worker.shutdown();
        super.onDestroy();
    }
}
