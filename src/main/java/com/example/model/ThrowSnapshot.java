package com.example.model;

import lombok.Getter;
import lombok.Setter;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

/**
 * Speichert den kompletten Spielzustand unmittelbar VOR einem Wurf.
 * "Rückgängig" stellt diesen Zustand 1:1 wieder her – unabhängig vom Spielmodus
 * und auch dann, wenn der Wurf ein Leg oder das Match beendet hat.
 */
@Getter
public class ThrowSnapshot {

    private final UUID playerId;
    private final ThrowResult throwResult;

    private final Map<UUID, Integer> scores;
    private final Map<UUID, Integer> wonLegs;

    private final UUID currentplayerId;
    private final int currentplayerIndex;
    private final int throwsleft;
    private final int legCounter;
    private final boolean gameover;
    private final boolean newLegStarted;

    // Wird nach der Verarbeitung gesetzt: hat der Wurf den Stand verändert (ATC: Ziel getroffen)?
    @Setter
    private boolean hit;

    public ThrowSnapshot(UUID playerId, ThrowResult throwResult, Match match) {
        GameState gs = match.getGameState();
        this.playerId = playerId;
        this.throwResult = throwResult;
        this.scores = new HashMap<>(match.getScores());
        this.wonLegs = new HashMap<>(match.getWonLegs());
        this.currentplayerId = gs.getCurrentplayerId();
        this.currentplayerIndex = gs.getCurrentplayerIndex();
        this.throwsleft = gs.getThrowsleft();
        this.legCounter = gs.getLegCounter();
        this.gameover = gs.isGameover();
        this.newLegStarted = gs.isNewLegStarted();
    }
}
