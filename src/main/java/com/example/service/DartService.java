package com.example.service;

import com.example.model.*;
import com.ibm.asyncutil.iteration.AsyncIterator;
import jakarta.enterprise.context.ApplicationScoped;

import java.util.*;
import java.util.stream.Collectors;

@ApplicationScoped
public class DartService {

    private final List<Player> players = new ArrayList<>();
    private Match match;

    public boolean addPlayer(String name) {
        if (players.stream().anyMatch(p -> p.getName().equals(name))) {
            return false;
        }
        else{
            players.add(new Player(name));
        }
       return true;
    }

    public List<Player> getPlayers() {
        return players;
    }

    public void resetPlayers()
    {
        this.players.clear();
    }
    public void deletePlayer(UUID id) {
        players.removeIf(p -> p.getId().equals(id));
    }


    public Map<UUID, Player> getPlayerMap() {
        return players.stream()
                .collect(Collectors.toMap(Player::getId, player -> player));
    }

    public void startNewMatch(List<UUID> playerIds, MatchMode mode, MatchConfig matchConfig, boolean isTeamMode) {
        this.match = new Match(playerIds, mode, matchConfig, isTeamMode);
    }

    public Match getMatch() {
        return match;
    }

    public void endMatch() {
        if (this.match != null) {
            this.match = null;
        }
    }

    // Gibt die Strategie des aktuellen Matches zurück (wird beim Match-Start festgelegt)
    private GameModeStrategy getStrategy() {
        return match.getStrategy();
    }

    public void processThrow(UUID playerId, ThrowResult throwResult) {
        GameState gameState = match.getGameState();

        if (!isValidThrow(playerId)) {
            throw new IllegalArgumentException("Invalid throw");
        }

        // Zustand vor dem Wurf sichern und Wurf speichern
        int scoreBefore = match.getScore(playerId);
        ThrowSnapshot snapshot = match.recordThrow(playerId, throwResult);

        gameState.setLastreset(false);
        gameState.setNewLegStarted(false);

        // Verarbeitung des Wurfs durch die jeweilige Strategie delegieren
        getStrategy().processThrow(match, playerId, throwResult);
        snapshot.setHit(gameState.isGameover() || match.getScore(playerId) != scoreBefore);

        // Check ob Leg beendet ist
        if (gameState.isGameover()) {
            if (!match.isMatchOver()) {
                resetLegScores();
            }
            return; // Leg / Match ist vorbei
        }

        // Nächster Spieler wenn keine Würfe mehr übrig sind
        if (gameState.getThrowsleft() == 0) {
            nextTurn();
        }
    }


    private boolean isValidThrow(UUID playerId) {
        GameState gamestate = match.getGameState();
        if (!(playerId.equals(gamestate.getCurrentplayerId()))) return false;
        if (gamestate.getThrowsleft() <= 0) return false;
        if (gamestate.isGameover()) return false;
        return true;
    }

    private void nextTurn() {
        GameState gamestate = match.getGameState();
        int nextPlayerIndex = (gamestate.getCurrentplayerIndex() + 1) % gamestate.getPlayOrder().size();
        UUID nextPlayerId = gamestate.getPlayOrder().get(nextPlayerIndex);

        gamestate.setThrowsleft(3);
        gamestate.setCurrentplayerId(nextPlayerId);
        gamestate.setCurrentplayerIndex(nextPlayerIndex);
    }

    private boolean firstThrow(UUID playerId) {
        return match.getScores().get(playerId) == 501;
    }

    private boolean validStartThrow(ThrowResult throwResult) {
        switch (match.getMode().getStartMode()) {
            case STRAIGHT_IN:
                return true;
            case DOUBLE_IN:
                return throwResult.isDouble();
            case MASTER_IN:
                return throwResult.isTriple() || throwResult.isDouble();
            default:
                return true;
        }
    }

    private boolean validEndThrow(ThrowResult throwResult) {
        switch (match.getMode().getEndMode()) {
            case STRAIGHT_OUT:
                return true;
            case DOUBLE_OUT:
                return throwResult.isDouble();
            case MASTER_OUT:
                return throwResult.isTriple() || throwResult.isDouble();
            default:
                return true;
        }
    }


    /*
    public void handleLeg(UUID winnerId){
        match.addWonLeg(winnerId);

        if(match.isMatchOver()){
            UUID matchWinner = match.getWinner();
        }
        else{
            resetLegScores();
        }
    }*/

    public void resetLegScores(){
        GameModeStrategy strategy = getStrategy();
        int startScore = strategy.getInitialScore();

        for (UUID playerId : match.getPlayerIds()) {
            match.setScore(playerId, startScore);
        }

        match.getGameState().setThrowsleft(3);
        match.getGameState().setGameover(false);
        match.getGameState().setNewLegStarted(true);
        match.getGameState().incrementsLegCounter();

        List<UUID> playOrder = match.getGameState().getPlayOrder();
        int starterIndex = match.getGameState().getLegCounter() % playOrder.size();
        match.getGameState().setCurrentplayerIndex(starterIndex);
        match.getGameState().setCurrentplayerId(playOrder.get(starterIndex));

    }


    // Macht den zuletzt geworfenen Dart rückgängig – egal von welchem Spieler,
    // auch wenn er ein Leg oder das Match beendet hat
    public boolean deleteLastThrow() {
        GameState gameState = match.getGameState();
        if (gameState.isLastreset()) return false;

        if (match.undoLastThrow()) {
            gameState.setLastreset(true);
            return true;
        }
        return false;
    }




    public Massages messagethrows(UUID playerId, ThrowResult throwResult) {
        if (match == null) return new Massages("Fehler", "Kein Spiel gestartet");
        return getStrategy().validateThrow(match, playerId, throwResult);
    }

}
