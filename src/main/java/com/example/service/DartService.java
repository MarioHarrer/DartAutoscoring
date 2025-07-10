package com.example.service;

import com.example.model.*;
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

    public void processThrow(UUID playerId, int score) {
        Match currentMatch = getMatch();
        GameState gameState = currentMatch.getGameState();

        if(!(isValidThrow(playerId, score))){
            throw new IllegalArgumentException("Invalid throw");
        }
        int currentScore = currentMatch.getScores().get(playerId);
        int newScore = currentScore - score;

        if(newScore == 0){
            currentMatch.getScores().put(playerId, newScore);
            gameState.setGameover(true);
            return;
        }

        if(newScore < 0){
            gameState.setThrowsleft(gameState.getThrowsleft() - 1);
        } else {
            currentMatch.getScores().put(playerId, newScore);
            gameState.setThrowsleft(gameState.getThrowsleft() - 1);
        }

        if(gameState.getThrowsleft() == 0){
            nextTurn();
        }
    }

    private boolean isValidThrow(UUID playerId, int score){
        GameState gamestate = match.getGameState();

        if(!(playerId.equals(gamestate.getCurrentplayerId()))){
            return false;
        }
        if(gamestate.getThrowsleft() <= 0){
            return false;
        }
        if(gamestate.isGameover()){
            return false;
        }
        return true;
    }

    private void nextTurn(){
        GameState gamestate = match.getGameState();

        int nextPlayerIndex = (gamestate.getCurrentplayerIndex() + 1) % gamestate.getPlayOrder().size();
        UUID nextPlayerId = gamestate.getPlayOrder().get(nextPlayerIndex);

        gamestate.setThrowsleft(3);
        gamestate.setCurrentplayerId(nextPlayerId);
        gamestate.setCurrentplayerIndex(nextPlayerIndex);
    }
}
