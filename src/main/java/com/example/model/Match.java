package com.example.model;

import lombok.Getter;

import java.time.LocalDateTime;
import java.util.*;

@Getter
public class Match {

    private final UUID id = UUID.randomUUID();
    private final List<UUID> playerIds;
    private final MatchMode mode;
    private final Map<UUID, Integer> scores = new HashMap<>();
    private final LocalDateTime startedAt = LocalDateTime.now();
    private final GameState gameState;
    private final Map<UUID, List<Integer>> playerThrows = new HashMap<>();

    public Match(List<UUID> playerIds, MatchMode mode) {
        this.playerIds = playerIds;
        this.mode = mode;
        this.gameState = new GameState(playerIds);

        int startScore = (mode.getType() == MatchModeType.MODE_501) ? 501 : 0;
        for (UUID playerId : playerIds) {
            scores.put(playerId, startScore);
            playerThrows.put(playerId, new ArrayList<>());
        }
    }

    public double getPlayerAverage(UUID playerId){
        List<Integer> shoots = this.playerThrows.get(playerId);
        if(shoots.isEmpty()){
            return 0.0;
        }
        int total = 0;
        for(Integer point : shoots){
            if(point != null){
                total += point;
            }
        }
        double average = (double)total / shoots.size();
        double rounded = Math.round(average * 100.0) / 100.0;
        return rounded;
    }
}
