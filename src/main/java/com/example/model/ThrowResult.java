package com.example.model;

import lombok.Getter;

@Getter
public class ThrowResult {

    private final int score;
    private final boolean isDouble;
    private final boolean isTriple;


    public ThrowResult(int score, boolean isDouble, boolean isTriple) {

        if(score == 50){
            this.score = 50;
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
