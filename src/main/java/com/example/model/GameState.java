package com.example.model;

import lombok.Getter;
import lombok.Setter;

import java.util.ArrayList;
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

    public GameState(List<UUID> players, boolean isTeamMode) {
        if (isTeamMode && players.size() == 4) {
            this.playOrder = new ArrayList<>();
            this.playOrder.add(players.get(0));
            this.playOrder.add(players.get(2));
            this.playOrder.add(players.get(1));
            this.playOrder.add(players.get(3));
        } else {
            this.playOrder = players;
        }
        this.currentplayerId = this.playOrder.get(0);
    }

    // Alter Konstruktor für Kompatibilität
    public GameState(List<UUID> players) {
        this(players, false);
    }

}
