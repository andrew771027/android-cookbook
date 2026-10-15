package com.example.androidcookbook.fixture;

import android.app.Activity;
import android.os.Bundle;
import android.widget.TextView;

public class MainActivity extends Activity{

    @overrider
    protected void onCreate(Bundle savedInstanceState){
        super.onCreate(savedInstanceState)

        TextView textView = new TextView(this);
        textView.setText("Android Cookbook Activity Fixture")
        textView.setTextSize(20);
        textView.setPadding(32, 48, 32, 32);

        setContentView(textView);
    }

}