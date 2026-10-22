package com.example.androidcookbook.fixture;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.util.Log;
import android.widget.TextView;

import java.util.UUID;

public class MainActivity extends Activity{

    private static final String TAG = "CookbookLifecycle";
    private static final String MARKER = "android-cookbook-v0.5.1";

    private final String instanceId = UUID.randomUUID().toString();

    private void recordLifecycle(String event){
        Log.i(
            TAG,
            "marker=" + MARKER
                    + " instance=" + instanceId
                    + " event=" + event
        );
    }

    @Override
    protected void onCreate(Bundle savedInstanceState){
        super.onCreate(savedInstanceState);

        recordLifecycle("onCreate");

        TextView textView = new TextView(this);
        textView.setText("Android Cookbook Activity Fixture");
        textView.setTextSize(20);
        textView.setPadding(32, 48, 32, 32);

        setContentView(textView);
    }

    @Override
    protected void onStart(){
        super.onStart();
        recordLifecycle("onStart");
    }

    @Override
    protected void onResume(){
        super.onResume();
        recordLifecycle("onResume");
    }

    @Override
    protected void onPause(){
        super.onPause();
        recordLifecycle("onPause");
    }

    @Override
    protected void onStop(){
        super.onStop();
        recordLifecycle("onStop");
    }

    @Override
    protected void onRestart(){
        super.onRestart();
        recordLifecycle("onRestart");
    }

    @Override
    protected void onDestroy(){
        super.onDestroy();
        recordLifecycle("onDestroy");
    }

    @Override
    protected void onNewIntent(Intent intent){
        super.onNewIntent(intent);

        if (intent.getBooleanExtra("cookbook_finish", false)){
            finish();
        }
    }

}
