package com.example.model;

import java.util.UUID;

public class Mode501Strategy implements GameModeStrategy{
    @Override
    public int getInitialScore() {
        return 501;
    }

    @Override
    public void processThrow(Match match, UUID playerId, ThrowResult throwResult) {
        GameState gameState = match.getGameState();
        int currentScore = match.getScore(playerId);
        int newScore = currentScore - throwResult.getScore();

        // Überworfen
        if (newScore < 0) {
            gameState.setThrowsleft(gameState.getThrowsleft() - 1);
            return;
        }

        // Check auf Finish
        if (newScore == 0) {
            if (isValidEndThrow(match, throwResult)) {
                match.setScore(playerId, 0);
                gameState.setGameover(true);
                match.addWonLeg(playerId);
                return;
            } else {
                // Falsches Finish (z.B. Single Out bei Double Out erzwingt Bust)
                gameState.setThrowsleft(gameState.getThrowsleft() - 1);
                return;
            }
        }

        // Regulärer Treffer
        match.setScore(playerId, newScore);
        gameState.setThrowsleft(gameState.getThrowsleft() - 1);
    }

    @Override
    public Massages validateThrow(Match match, UUID playerId, ThrowResult throwResult) {
        int currentScore = match.getScore(playerId);
        int newscore = currentScore - throwResult.getScore();

        if (newscore < 0) {
            return new Massages("Ungültiger Wurf", "Überworfen");
        }

        if (currentScore == 501) {
            switch (match.getMode().getStartMode()) {
                case DOUBLE_IN:
                    if (!throwResult.isDouble()) return new Massages("Ungültiger Wurf", "Du musst mit Double beginnen");
                    break;
                case MASTER_IN:
                    if (!throwResult.isTriple() && !throwResult.isDouble()) return new Massages("Ungültiger Wurf", "Du musst mit Triple oder Double beginnen");
                    break;
            }
        }

        if (newscore == 0) {
            switch (match.getMode().getEndMode()) {
                case DOUBLE_OUT:
                    if (!throwResult.isDouble()) return new Massages("Ungültiger Wurf", "Du musst mit Double enden");
                    break;
                case MASTER_OUT:
                    if (!throwResult.isTriple() && !throwResult.isDouble()) return new Massages("Ungültiger Wurf", "Du musst mit Triple oder Double enden");
                    break;
            }
        }

        if((match.getMode().getEndMode() == EndMode.MASTER_OUT || match.getMode().getEndMode() == EndMode.DOUBLE_OUT) && newscore == 1){
            return new Massages("Ungültiger Wurf", "1 Punkt in Double/Triple out Modus nicht erlaubt");
        }

        return new Massages("OK", "Wurf erfolgreich", true);
    }

    private boolean isValidEndThrow(Match match, ThrowResult throwResult) {
        switch (match.getMode().getEndMode()) {
            case DOUBLE_OUT: return throwResult.isDouble();
            case MASTER_OUT: return throwResult.isTriple() || throwResult.isDouble();
            default: return true;
        }
    }
}
