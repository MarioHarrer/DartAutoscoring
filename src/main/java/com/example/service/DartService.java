package com.example.service;

import com.example.model.Match;
import com.example.model.MatchMode;
import com.example.model.Player;
import jakarta.enterprise.context.ApplicationScoped;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.stream.Collectors;

@ApplicationScoped
public class DartService {

    private final List<Player> players = new ArrayList<>();
    private Match match;

    public void addPlayer(String name) {
        players.add(new Player(name));
    }

    public List<Player> getPlayers() {
        return players;
    }

    public Map<UUID, Player> getPlayerMap() {
        return players.stream()
                .collect(Collectors.toMap(Player::getId, player -> player));
    }

    public void startNewMatch(List<UUID> playerIds, MatchMode mode) {
        this.match = new Match(playerIds, mode);
    }

    public Match getMatch() {
        return match;
    }
}
