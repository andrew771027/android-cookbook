package com.example.androidcookbook.fixture;

import android.app.Activity;
import android.content.Intent;
import android.content.res.Configuration;
import android.os.Bundle;
import android.util.Log;
import android.widget.TextView;
import android.os.Process;

import java.util.UUID;

public class MainActivity extends Activity{

    private static final String LIFECYCLE_TAG = "CookbookLifecycle";
    private static final String STATE_TAG = "CookbookState";

    private static final String LIFECYCLE_MARKER = "android-cookbook-v0.5.1";
    private static final String STATE_MARKER = "android-cookbook-v0.5.2";

    private static final String KEY_COUNTER = "counter";

    private final String instanceId = UUID.randomUUID().toString();

    private int counter = 0;

    private TextView textView;

    private String orientationName(){
        int orientation = getResources()
                .getConfiguration()
                .orientation;

        if (orientation == Configuration.ORIENTATION_LANDSCAPE){
            return "landscape";
        }

        if (orientation == Configuration.ORIENTATION_PORTRAIT){
            return "portrait";
        }

        return "undefined";

    }

    private void logLifecycle(String event){
        Log.i(
            LIFECYCLE_TAG,
            "marker=" + LIFECYCLE_MARKER
                    + " instance=" + instanceId
                    + " event=" + event
        );
    }

    private void logState(String event, boolean restored){
        Log.i(
            STATE_TAG,
            "marker=" + STATE_MARKER
                    + " instance=" + instanceId
                    + " event=" + event
                    + " counter=" + counter
                    + " orientation=" + orientationName()
                    + " restored=" + restored
                    + " pid=" + Process.myPid()
        );
    }

    private void updateUI(){
        if (textView != null){
            textView.setText(
                "Android Cookbook v0.5.2\n"
                    + "Counter: " + counter + "\n"
                    + "Orientation: " + orientationName()
            );
        }
    }

    @Override
    protected void onCreate(Bundle savedInstanceState){
        super.onCreate(savedInstanceState);

        logLifecycle("onCreate");

        boolean restored = savedInstanceState != null;

        if (restored){
            counter = savedInstanceState.getInt(
                KEY_COUNTER,
                0
            );
        }

        textView = new TextView(this);
        textView.setTextSize(20);
        textView.setPadding(32, 48, 32, 32);

        setContentView(textView);
        updateUI();

        logState("created", restored);
    }

    @Override
    protected void onStart(){
        super.onStart();
        logLifecycle("onStart");
    }

    @Override
    protected void onResume(){
        super.onResume();
        logLifecycle("onResume");
        logState("resumed", false);
    }

    @Override
    protected void onPause(){
        logLifecycle("onPause");
        super.onPause();
    }

    @Override
    protected void onStop(){
        logLifecycle("onStop");
        super.onStop();
    }

    @Override
    protected void onRestart(){
        logLifecycle("onRestart");
        super.onRestart();
    }

    @Override
    protected void onSaveInstanceState(Bundle outState){
        outState.putInt(KEY_COUNTER, counter);

        logState("saved", false);

        super.onSaveInstanceState(outState);
    }

    @Override
    protected void onDestroy(){
        logLifecycle("onDestroy");
        super.onDestroy();
    }

    @Override
    protected void onNewIntent(Intent intent){
        super.onNewIntent(intent);
        setIntent(intent);

        if (intent.getBooleanExtra("cookbook_finish", false)){
            finish();
        }

        String action = intent.getStringExtra("cookbook_action");

        if ("increment".equals(action)){
            counter += 1;
            updateUI();
            logState("incremented", false);
        }

        if ("report".equals(action)){
            logState("reported", false);
        }
    }

}
