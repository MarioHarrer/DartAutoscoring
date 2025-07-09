package com.example.model;

import lombok.Getter;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@Getter
public class Match {

    private final UUID id = UUID.randomUUID();
    private final List<UUID> playerIds;
    private final MatchMode mode;
    private final Map<UUID, Integer> scores = new HashMap<>();
    private final LocalDateTime startedAt = LocalDateTime.now();

    public Match(List<UUID> playerIds, MatchMode mode) {
        this.playerIds = playerIds;
        this.mode = mode;

        int startScore = (mode.getType() == MatchModeType.MODE_501) ? 501 : 0;
        for (UUID playerId : playerIds) {
            scores.put(playerId, startScore);
        }
    }
}
