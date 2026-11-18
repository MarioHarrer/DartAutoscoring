package com.example.model;

import java.util.UUID;

public class ModeATCStrategy implements GameModeStrategy{

    // Nach der 20 muss noch das Bull getroffen werden (Outer oder Inner Bull, Segment 25)
    public static final int LAST_NUMBER = 20;
    public static final int BULL = 25;

    @Override
    public int getInitialScore() {
        return 1;
    }

    @Override
    public void processThrow(Match match, UUID playerId, ThrowResult throwResult) {
        GameState gameState = match.getGameState();
        int targetSegment = match.getScore(playerId);

        // Wenn das getroffene Segment der Ziel-Zahl entspricht
        if (throwResult.getSegment() == targetSegment && throwResult.getScore() != 0) {
            if (targetSegment == BULL) {
                // Spieler hat das Bull getroffen und damit gewonnen
                gameState.setGameover(true);
                match.addWonLeg(playerId);
            } else if (targetSegment == LAST_NUMBER) {
                // 20 getroffen -> jetzt muss das Bull getroffen werden
                match.setScore(playerId, BULL);
            } else {
                // Ziel getroffen -> Nächste Zahl
                match.setScore(playerId, targetSegment + 1);
            }
        }

        gameState.setThrowsleft(gameState.getThrowsleft() - 1);
    }

    @Override
    public Massages validateThrow(Match match, UUID playerId, ThrowResult throwResult) {
        int targetSegment = match.getScore(playerId);

        if (throwResult.getScore() == 0) {
            return new Massages("Miss", "Daneben geworfen", true);
        }

        if (throwResult.getSegment() == targetSegment) {
            String text = targetSegment == BULL ? "Bull getroffen" : "Zahl " + targetSegment + " getroffen";
            return new Massages("Treffer!", text, true);
        } else {
            String text = targetSegment == BULL ? "Du musst auf das Bull werfen" : "Du musst auf die " + targetSegment + " werfen";
            return new Massages("Daneben", text, true);
        }
    }

    // Anzeige der Ziel-Zahl im Frontend ("Bull" statt 25)
    public static String targetLabel(int target) {
        return target == BULL ? "Bull" : String.valueOf(target);
    }
}
