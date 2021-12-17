package com.example.yuv_resolve;

import android.graphics.Rect;
import android.graphics.YuvImage;
import android.hardware.Camera;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.OutputStream;
import java.net.Socket;
import java.util.Arrays;

public class MyPreviewCallBack implements Camera.PreviewCallback {
    Socket socket=null;
    OutputStream oss;
    boolean transferring=false;
    int sleep_time;
    String ip_add = "192.168.1.120";
//    String ip_add = "172.16.0.1";

    public MyPreviewCallBack(String message) throws InterruptedException {
        Thread thread=new Thread(){
            @Override
            public void run() {
                super.run();
                if(socket==null){
                    //1.创建监听指定服务器地址以及指定服务器监听的端口号
                    try {
                        socket = new Socket(ip_add, 24999);//111.111.11.11为我这个本机的IP地址，端口号为12306.

                    } catch (IOException e) {
                        e.printStackTrace();
                    }
                }
            }
        };
        thread.start();
        thread.join(4000);
        sleep_time=Integer.parseInt(message);
    }

    @Override
    protected void finalize() throws Throwable {
        super.finalize();
        try {
            socket.shutdownOutput();
            oss.close();
            socket.close();
            socket = null;
            oss=null;
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    private int cnt=0;
    @Override
    public synchronized void onPreviewFrame(byte[] data, Camera camera) {
        System.out.println(123);
        previewChange(data, camera);
    }
    public synchronized void previewChange(byte[] data, Camera camera){
//        try {
//            Thread.sleep(60);
//        } catch (InterruptedException e) {
//            e.printStackTrace();
//        }
        if(transferring){
            return;
        }
//        if(cnt>1000){
//            return;
//        }
        transferring=true;
        cnt++;
        System.out.println(cnt);

        Camera.Parameters parameters = camera.getParameters();
        Camera.Size size = parameters.getPreviewSize();
        YuvImage image = new YuvImage(data, parameters.getPreviewFormat(),
                size.width, size.height, null);
//        File file = new File(Environment.getExternalStorageDirectory()
//                .getPath() + "/out.jpg");
//        FileOutputStream filecon = new FileOutputStream(file);
//        oss = socket.getOutputStream();
//        ByteArrayOutputStream stream = new ByteArrayOutputStream();
//        image.compressToJpeg(
//                new Rect(0, 0, image.getWidth(), image.getHeight()), 90,
//                stream);
//        byte[] byteArray=stream.toByteArray();
//        System.out.println(byteArray.length);
//        System.out.println("hahauyie21");
//        System.out.println(Arrays.toString(byteArray).length());
        try {
            Thread.sleep(sleep_time);
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
//        System.out.println(Arrays.toString(data).length());
        Thread s_thread = new Thread(){
            @Override
            public synchronized void run() {
                super.run();
                try {
                    image.compressToJpeg(
                            new Rect(0, 0, image.getWidth(), image.getHeight()), 90,
                            socket.getOutputStream());
//                    socket.shutdownOutput();
//                    socket.getOutputStream().flush();
                } catch (IOException e) {
                    e.printStackTrace();
                }
                transferring=false;
            }
        };
        s_thread.start();
        try {
            s_thread.join(10000);
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
    }
}
