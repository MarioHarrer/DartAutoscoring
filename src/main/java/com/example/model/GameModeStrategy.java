package com.example.model;

import java.util.UUID;

public interface GameModeStrategy {
    int getInitialScore();
    void processThrow(Match match, UUID playerId, ThrowResult throwResult);
    Massages validateThrow(Match match, UUID playerId, ThrowResult throwResult);

    // Liefert die passende Strategie zum Spielmodus
    static GameModeStrategy forType(MatchModeType type) {
        if (type == MatchModeType.MODE_AROUND_THE_CLOCK) {
            return new ModeATCStrategy();
        }
        return new Mode501Strategy();
    }
}
