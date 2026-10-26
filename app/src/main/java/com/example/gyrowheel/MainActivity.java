package com.example.gyrowheel;

import android.hardware.Sensor;
import android.hardware.SensorEvent;
import android.hardware.SensorEventListener;
import android.hardware.SensorManager;
import android.os.Bundle;
import android.widget.Button;
import android.widget.EditText;
import android.widget.TextView;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;

import okhttp3.*;
import java.util.concurrent.TimeUnit;
import org.json.JSONObject;

public class MainActivity extends AppCompatActivity implements SensorEventListener {
    private EditText ipInput;
    private TextView tvStatus;
    private Button btnConnect, btnCalibrate, btnGas;
    private SensorManager sensorManager;
    
    private WebSocket webSocket = null;
    private OkHttpClient client;
    private boolean isConnected = false;
    
    private float baseGamma = 0;
    private boolean isCalibrated = false;
    private boolean isGasPressed = false;

    @Override
    protected void onCreate(Bundle b) {
        super.onCreate(b);
        setContentView(R.layout.activity_main);

        ipInput = findViewById(R.id.ipInput);
        tvStatus = findViewById(R.id.tvStatus);
        btnConnect = findViewById(R.id.btnConnect);
        btnCalibrate = findViewById(R.id.btnCalibrate);
        btnGas = findViewById(R.id.btnGas);

        client = new OkHttpClient.Builder().readTimeout(0, TimeUnit.MILLISECONDS).build();
        sensorManager = (SensorManager) getSystemService(SENSOR_SERVICE);

        btnConnect.setOnClickListener(v -> {
            if (isConnected) return;
            String ip = ipInput.getText().toString().trim();
            if (ip.isEmpty()) { Toast.makeText(this, "Введите IP", Toast.LENGTH_SHORT).show(); return; }
            connectWebSocket(ip);
        });

        btnCalibrate.setOnClickListener(v -> {
            isCalibrated = false;
            tvStatus.setText("Калибровка...");
            tvStatus.setTextColor(0xFFFFAA00);
        });

        btnGas.setOnTouchListener((v, event) -> {
            if (event.getAction() == android.view.MotionEvent.ACTION_DOWN) {
                isGasPressed = true;
                btnGas.setBackgroundTintList(android.content.res.ColorStateList.valueOf(0xFFFF0000));
            } else if (event.getAction() == android.view.MotionEvent.ACTION_UP) {
                isGasPressed = false;
                btnGas.setBackgroundTintList(android.content.res.ColorStateList.valueOf(0xFF00FF00));
            }
            return true;
        });
    }

    private void connectWebSocket(String ip) {
        Request request = new Request.Builder().url("ws://" + ip + ":8080").build();
        webSocket = client.newWebSocket(request, new WebSocketListener() {
            @Override
            public void onOpen(WebSocket webSocket, Response response) {
                runOnUiThread(() -> {
                    isConnected = true;
                    tvStatus.setText("ПОДКЛЮЧЕНО");
                    tvStatus.setTextColor(0xFF00FF00);
                    Toast.makeText(MainActivity.this, "Руль подключен!", Toast.LENGTH_SHORT).show();
                });
            }

            @Override
            public void onFailure(WebSocket webSocket, Throwable t, Response response) {
                runOnUiThread(() -> {
                    isConnected = false;
                    tvStatus.setText("ОШИБКА");
                    tvStatus.setTextColor(0xFFFF0000);
                });
            }
        });
    }

    @Override
    protected void onResume() {
        super.onResume();
        sensorManager.registerListener(this, sensorManager.getDefaultSensor(Sensor.TYPE_GAME_ROTATION_VECTOR), SensorManager.SENSOR_DELAY_GAME);
    }

    @Override
    protected void onPause() {
        super.onPause();
        sensorManager.unregisterListener(this);
    }

    @Override
    public void onSensorChanged(SensorEvent event) {
        if (event.sensor.getType() != Sensor.TYPE_GAME_ROTATION_VECTOR) return;

        float[] rotationMatrix = new float[9];
        SensorManager.getRotationMatrixFromVector(rotationMatrix, event.values);
        float[] orientation = new float[3];
        SensorManager.getOrientation(rotationMatrix, orientation);

        float currentGamma = (float) Math.toDegrees(orientation[2]);

        if (!isCalibrated) {
            baseGamma = currentGamma;
            isCalibrated = true;
            runOnUiThread(() -> {
                tvStatus.setText("ГОТОВ К ИГРЕ");
                tvStatus.setTextColor(0xFF00FF00);
            });
        }

        if (!isConnected || webSocket == null) return;

        float steer = (currentGamma - baseGamma) / 30.0f;
        steer = Math.max(-1f, Math.min(1f, steer));
        float throttle = isGasPressed ? 1.0f : 0.0f;

        try {
            JSONObject json = new JSONObject();
            json.put("steer", steer);
            json.put("throttle", throttle);
            webSocket.send(json.toString());
        } catch (Exception e) {}
    }

    @Override
    public void onAccuracyChanged(Sensor sensor, int accuracy) {}
}
