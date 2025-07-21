package com.example.model;


import lombok.Getter;

@Getter
public class MatchConfig {
    private final GameType gameType;
    private final int targetvalue;


    public MatchConfig(GameType gameType, int targetvalue) {
        this.gameType = gameType;
        this.targetvalue = targetvalue;
    }

}
