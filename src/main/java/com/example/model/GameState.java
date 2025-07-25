package com.example.model;

import lombok.Getter;
import lombok.Setter;

import java.util.List;
import java.util.UUID;

@Getter
@Setter
public class GameState {
    private UUID currentplayerId;
    private int currentScore;
    private int throwsleft = 3;
    private boolean isGameover;
    private List<UUID> playOrder;
    private int currentplayerIndex = 0;
    private int legCounter = 0;
    private boolean lastreset = false;
    private boolean newLegStarted = true;

    public void incrementsLegCounter(){
        this.legCounter++;
    }

    public GameState(List<UUID> players) {
        this.playOrder = players;
        this.currentplayerId = players.get(0);
    }
}
