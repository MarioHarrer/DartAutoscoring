package com.example.model;

import lombok.Getter;

@Getter
public class ThrowResult {

    private final int score;     // Gesamtpunkte für 501 (z.B. 60 bei Triple 20)
    private final int segment;   // Getroffenes Feld für Around the Clock (z.B. 20 bei Triple 20)
    private final boolean isDouble;
    private final boolean isTriple;

    public ThrowResult(int rawInput, boolean isDouble, boolean isTriple) {
        this.isDouble = isDouble;
        this.isTriple = isTriple;

        if (rawInput == 50 && isDouble) {
            // Inner Bull / Bullseye
            this.segment = 25;
            this.score = 50;
        } else if (isTriple) {
            // Triple (z.B. Feld 20 -> Segment 20, Score 60)
            this.segment = rawInput;
            this.score = rawInput * 3;
        } else if (isDouble) {
            // Double (z.B. Feld 20 -> Segment 20, Score 40)
            this.segment = rawInput;
            this.score = rawInput * 2;
        } else {
            // Single / Outer Bull / Miss
            this.segment = rawInput;
            this.score = rawInput;
        }
    }
}