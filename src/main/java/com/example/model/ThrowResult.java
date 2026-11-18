package com.example.model;

import lombok.Getter;

@Getter
public class ThrowResult {

    private final int score;
    private final boolean isDouble;
    private final boolean isTriple;

    public ThrowResult(int score, boolean isDouble, boolean isTriple) {
        // Bullseye (50) und Single Bull (25) dürfen nicht multipliziert werden
        if(score == 50 || score == 25){
            this.score = score;
        }
        else{
            int finalScore = score;
            if (isDouble) {
                finalScore *= 2;
            } else if (isTriple) {
                finalScore *= 3;
            }
            this.score = finalScore;
        }
        this.isDouble = isDouble;
        this.isTriple = isTriple;
    }
}