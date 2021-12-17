package com.example.yuv_resolve;

import androidx.appcompat.app.AppCompatActivity;

import android.content.Intent;
import android.hardware.Camera;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.FrameLayout;

import java.io.OutputStream;
import java.net.Socket;

public class CameraPreview extends AppCompatActivity {

    static Camera mCamera = null;
    private CameraPreviewJava mPreview;
    private String TAG = "source";

    String message;

    Socket socket=null;
    OutputStream os;

    public static final int MEDIA_TYPE_IMAGE = 1;
    public static final int MEDIA_TYPE_VIDEO = 2;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_camera_preview);

        Intent intent = getIntent();
        message = intent.getStringExtra(MainActivity.EXTRA_MESSAGE);

        try {
            initCamera();
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
    }

    public void initCamera() throws InterruptedException {
        // Create an instance of Camera
        mCamera = getCameraInstance();

        // Create our Preview view and set it as the content of our activity.
        mPreview = new CameraPreviewJava(this, mCamera);
        FrameLayout preview = (FrameLayout) findViewById(R.id.camera_preview);
        preview.addView(mPreview);
        mCamera.setPreviewCallback(new MyPreviewCallBack(message));
        Camera.Parameters params=mCamera.getParameters();
        params.setPreviewSize(640,480);
//        params.setPreviewFormat(ImageFormat.YV12);
        mCamera.setParameters(params);
    }

//    public void preview(){
//        mCamera.
//    }

    /** A safe way to get an instance of the Camera object. */
    public static Camera getCameraInstance(){
        Camera c = null;
        try {
            c = Camera.open(); // attempt to get a Camera instance
        }
        catch (Exception e){
            // Camera is not available (in use or does not exist)
            throw e;
        }
        return c; // returns null if camera is unavailable
    }
}