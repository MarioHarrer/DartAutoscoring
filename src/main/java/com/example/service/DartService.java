package com.example.service;

import com.example.model.*;
import com.ibm.asyncutil.iteration.AsyncIterator;
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
    public void deletPlayer(String name){
        for(Player p : players){
            if(p.getName().equals(name)){
                players.remove(p);
                return;
            }
        }
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

    public void processThrow(UUID playerId, ThrowResult throwResult) {
        Match currentMatch = getMatch();
        GameState gameState = currentMatch.getGameState();


        if (!(isValidThrow(playerId, throwResult))) {
            throw new IllegalArgumentException("Invalid throw");
        }

        if (firstThrow(playerId) && !validStartThrow(throwResult)) {
            gameState.setThrowsleft(gameState.getThrowsleft() - 1);
            currentMatch.getPlayerThrows().get(playerId).add(0);                    //Den Wurf auch wenn er 0 Punkte hat speichern
            if (gameState.getThrowsleft() == 0) {
                nextTurn();
            }
            return;
        }

        int throwscore = throwResult.getScore();
        int currentScore = currentMatch.getScores().get(playerId);
        int newScore = currentScore - throwResult.getScore();

        currentMatch.getPlayerThrows().get(playerId).add(throwscore);

        if (newScore == 0) {
            if (validEndThrow(throwResult)) {
                currentMatch.getScores().put(playerId, 0);
                gameState.setGameover(true);
                return;
            } else {
                gameState.setThrowsleft(gameState.getThrowsleft() - 1);
                if (gameState.getThrowsleft() == 0 && !gameState.isGameover()) {
                    nextTurn();
                }
                return;
            }
        }

        if (newScore < 0) {
            gameState.setThrowsleft(gameState.getThrowsleft() - 1);
        } else {
            currentMatch.getScores().put(playerId, newScore);
            gameState.setThrowsleft(gameState.getThrowsleft() - 1);

            if (newScore == 0) {
                gameState.setGameover(true);
            }
        }

        if (gameState.getThrowsleft() == 0 && !gameState.isGameover()) {
            nextTurn();
        }
    }

    private boolean isValidThrow(UUID playerId, ThrowResult throwResult) {
        GameState gamestate = match.getGameState();

        if (!(playerId.equals(gamestate.getCurrentplayerId()))) {
            return false;
        }
        if (gamestate.getThrowsleft() <= 0) {
            return false;
        }
        if (gamestate.isGameover()) {
            return false;
        }
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

    public void endMatch() {
        if (this.match != null) {
            this.match = null;
        }
    }

    public Massages messagethrows(UUID playerId, ThrowResult throwResult) {
        Match currentmatch = getMatch();
        GameState gameState = currentmatch.getGameState();

        if (currentmatch == null) {
            return new Massages("Fehler", "Kein Spiel gestartet");
        }
        int currentscore = currentmatch.getScores().get(playerId);
        int newscore = currentscore - throwResult.getScore();

        if (newscore < 0) {
            return new Massages("Ungültiger Wurf", "Überworfen");
        }


        if (firstThrow(playerId)) {
            switch (currentmatch.getMode().getStartMode()) {
                case DOUBLE_IN:
                    if (!throwResult.isDouble()) {
                        return new Massages("Ungültiger Wurf", "Du musst mit Double oder Bull's Eye beginnen");
                    }
                    break;
                case MASTER_IN:
                    if (!throwResult.isTriple() && !throwResult.isDouble()) {
                        return new Massages("Ungültiger Wurf", "Du musst mit Triple, Double oder Bull's Eye beginnen");
                    }
                    break;
            }
        }
        if (newscore == 0) {
            switch (currentmatch.getMode().getEndMode()) {
                case DOUBLE_OUT:
                    if (!throwResult.isDouble()) {
                        return new Massages("Ungültiger Wurf", "Du musst mit Double oder Bull's Eye enden");
                    }
                case MASTER_OUT:
                    if (!throwResult.isTriple() && !throwResult.isDouble()) {
                        return new Massages("Ungültiger Wurf", "Du musst mit Triple, Double oder Bull's Eye enden");
                    }
            }
        }
        if((currentmatch.getMode().getEndMode() == EndMode.MASTER_OUT || currentmatch.getMode().getEndMode() == EndMode.DOUBLE_OUT) && newscore == 1){
            return new Massages("Ungültiger Wurf", "1 Punkt in Double/Triple out Modus nicht erlaubt");
        }
        return new Massages("OK", "Wurf erfolgreich", true);
    }

}
