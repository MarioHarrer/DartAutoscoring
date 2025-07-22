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
    private final MatchConfig matchConfig;
    private final Map<UUID, Integer> wonLegs = new HashMap<>();

    public Match(List<UUID> playerIds, MatchMode mode, MatchConfig matchConfig) {
        this.playerIds = playerIds;
        this.mode = mode;
        this.matchConfig = matchConfig;
        this.gameState = new GameState(playerIds);

        int startScore = (mode.getType() == MatchModeType.MODE_501) ? 501 : 0;
        for (UUID playerId : playerIds) {
            scores.put(playerId, startScore);
            playerThrows.put(playerId, new ArrayList<>());
            wonLegs.put(playerId, 0);
        }
    }

    public double getPlayerAverage(UUID playerId){
        List<Integer> shoots = this.playerThrows.get(playerId);
        if(shoots.isEmpty()){
            return 0.0;
        }

        int total = 0;
        int roundsof3 = (shoots.size() / 3) * 3;

        for(int i = 0; i < roundsof3; i++){
            if(shoots.get(i) != null){
                total += shoots.get(i);
            }
        }
        double average = roundsof3 > 0 ? (double)total / (double)roundsof3 : 0.0;
        return Math.round(average * 100.0) / 100.0;
    }

    public int getThrows(UUID playerId){
        return playerThrows.get(playerId).size();
    }

    public boolean isDraw(){
        if(matchConfig == null || matchConfig.getGameType() != GameType.BEST_OF){
            return false;
        }


        Iterator<Integer> iterator = wonLegs.values().iterator();
        int referenceWins = iterator.next();

        boolean sameWins = true;
        for(int wins : wonLegs.values()){
            if(wins != referenceWins){
                sameWins = false;
                break;
            }
        }

        int totalWins = 0;
        for(int wins : wonLegs.values()){
            totalWins += wins;
        }
        boolean totallegsreached = totalWins >= matchConfig.getTargetvalue();

        return sameWins && totallegsreached;
    }



    public boolean isMatchOver(){
        if(matchConfig == null){
            return false;
        }

        switch (matchConfig.getGameType()) {
            case BEST_OF:
                if(isDraw()){
                    return true;
                }
                int neededWins = (matchConfig.getTargetvalue() / 2) + 1;
                return wonLegs.values().stream().anyMatch(wins -> wins >= neededWins);
            case FIRST_TO:
                return wonLegs.values().stream().anyMatch(wins -> wins >= matchConfig.getTargetvalue());
            default:
                return false;
        }
    }

    /*public UUID getWinner(){
        if(!isMatchOver()){
            return null;
        }
        if(isDraw()){
            return null;
        }
       return wonLegs.entrySet().stream()
               .max(Map.Entry.comparingByValue())
               .map(Map.Entry::getKey)
               .orElse(null);
    }*/

    public void addWonLeg(UUID playerId){
        wonLegs.merge(playerId, 1, Integer::sum);
    }
}
