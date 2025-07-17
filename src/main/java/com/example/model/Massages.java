package com.example.model;

public class Massages {
    private String title;
    private String text;
    private boolean valid;

    public Massages(String title, String text) {
        this.title = title;
        this.text = text;
        this.valid = false;
    }

    public Massages(String title, String text, boolean valid) {
        this.title = title;
        this.text = text;
        this.valid = valid;
    }

    public String getTitle() { return title; }
    public String getText() { return text; }
    public boolean isValid() { return valid; }

}
