package com.example.model;

import lombok.Getter;

import java.io.*;
import java.nio.charset.StandardCharsets;
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
    private final boolean isTeamMode;


    private final Map<UUID, UUID> playerTeamMap = new HashMap<>(); // Speichert die Team-Zuordnung

    public Match(List<UUID> playerIds, MatchMode mode, MatchConfig matchConfig, boolean isTeamMode) {
        this.playerIds = playerIds;
        this.mode = mode;
        this.matchConfig = matchConfig;
        this.gameState = new GameState(playerIds, isTeamMode);
        this.isTeamMode = isTeamMode;

        if (isTeamMode && playerIds.size() == 4) {
            // Team 1: Spieler 0 und 1
            playerTeamMap.put(playerIds.get(0), playerIds.get(0)); // Team-Leader ist erster Spieler
            playerTeamMap.put(playerIds.get(1), playerIds.get(0));

            // Team 2: Spieler 2 und 3
            playerTeamMap.put(playerIds.get(2), playerIds.get(2)); // Team-Leader ist dritter Spieler
            playerTeamMap.put(playerIds.get(3), playerIds.get(2));
        }

        int startScore = (mode.getType() == MatchModeType.MODE_501) ? 501 : 0;

        for (UUID playerId : playerIds) {
            scores.put(playerId, startScore);
            playerThrows.put(playerId, new ArrayList<>());
            wonLegs.put(playerId, 0);
        }
    }

    public int getScore(UUID playerId) {
        if (isTeamMode) {
            return scores.get(playerTeamMap.get(playerId));
        }
        return scores.get(playerId);
    }

    public void setScore(UUID playerId, int score) {
        if (isTeamMode) {
            UUID teamLeader = playerTeamMap.get(playerId);
            scores.put(teamLeader, score);
            // Aktualisiere auch den Score des Teammitglieds
            for (UUID pid : playerIds) {
                if (playerTeamMap.get(pid).equals(teamLeader)) {
                    scores.put(pid, score);
                }
            }
        } else {
            scores.put(playerId, score);
        }
    }

    public int getWonLegs(UUID playerId) {
        if (isTeamMode) {
            return wonLegs.get(playerTeamMap.get(playerId));
        }
        return wonLegs.get(playerId);
    }

    public void addWonLeg(UUID playerId) {
        if (isTeamMode) {
            UUID teamLeader = playerTeamMap.get(playerId);
            wonLegs.merge(teamLeader, 1, Integer::sum);
            // Aktualisiere auch die Legs des Teammitglieds
            for (UUID pid : playerIds) {
                if (playerTeamMap.get(pid).equals(teamLeader)) {
                    wonLegs.put(pid, wonLegs.get(teamLeader));
                }
            }
        } else {
            wonLegs.merge(playerId, 1, Integer::sum);
        }
    }




    public double getPlayerAverage(UUID playerId) {
        List<Integer> shoots = this.playerThrows.get(playerId);
        if (shoots.isEmpty()) {
            return 0.0;
        }

        int total = 0;
        int roundsof3 = shoots.size() / 3;

        for (int i = 0; i < roundsof3 * 3; i++) {
            if (shoots.get(i) != null) {
                total += shoots.get(i);
            }
        }

        double average = roundsof3 > 0 ? (double)total / roundsof3 : 0.0;
        return Math.round(average * 100.0) / 100.0;
    }


    public int getThrows(UUID playerId){
        return playerThrows.get(playerId).size();
    }

    public boolean isDraw(){

        if(playerIds.size() == 1){
            return false;
        }

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

    public UUID getWinner() {
        if (!isMatchOver()) {
            return null;
        }
        if (isDraw()) {
            return null;
        }

        if (isTeamMode) {
            // Finde den Spieler mit den meisten gewonnenen Legs
            UUID winningPlayer = wonLegs.entrySet().stream()
                    .max(Map.Entry.comparingByValue())
                    .map(Map.Entry::getKey)
                    .orElse(null);

            // Wenn wir einen Gewinner haben, geben wir sein Team zurück (also seinen Team-Zuordnungs-ID)
            if (winningPlayer != null) {
                return playerTeamMap.get(winningPlayer);
            }
            return null;
        } else {
            // Im Einzelspieler-Modus wie bisher
            return wonLegs.entrySet().stream()
                    .max(Map.Entry.comparingByValue())
                    .map(Map.Entry::getKey)
                    .orElse(null);
        }
    }


   /* public void startKameraTest() {
        try {
            String projectPath = System.getProperty("user.dir");
            String scriptPath = projectPath + "/camera/kamera_test.py";

            ProcessBuilder processBuilder = new ProcessBuilder("python", scriptPath);
            processBuilder.redirectErrorStream(true);

            System.out.println("Starte Python-Skript: " + scriptPath);
            Process process = processBuilder.start();

            // Schreiben zum Python-Skript
            try (BufferedWriter writer = new BufferedWriter(
                    new OutputStreamWriter(process.getOutputStream()));
                 BufferedReader reader = new BufferedReader(
                         new InputStreamReader(process.getInputStream()))) {

                // Beispiel: Senden von Befehlen an das Python-Skript
                writer.write("start");
                writer.newLine();
                writer.flush();

                // Lesen der Antworten
                String line;
                while ((line = reader.readLine()) != null) {
                    System.out.println("Python-Ausgabe: " + line);
                    // Verarbeitung der Python-Ausgabe
                }
            }

            int exitCode = process.waitFor();
            if (exitCode != 0) {
                throw new IOException("Python-Skript wurde mit Fehlercode beendet: " + exitCode);
            }

        } catch (IOException | InterruptedException e) {
            System.err.println("Fehler beim Ausführen des Python-Skripts: " + e.getMessage());
            throw new RuntimeException(e);
        }
    }*/

    //Absoluter path:


    public void startKameraTest() {
    try {
        // Absoluter Pfad
        String scriptPath = "C:\\Users\\harrerm\\IdeaProjects\\DartAutoscoring\\camera\\kamera_test.py";

        File scriptFile = new File(scriptPath);
        if (!scriptFile.exists()) {
            System.err.println("Python-Skript nicht gefunden: " + scriptPath);
            return;
        }

        System.out.println("Versuche Python-Skript zu starten von: " + scriptPath);

        ProcessBuilder processBuilder = new ProcessBuilder("python", scriptPath);
        // Arbeitsverzeichnis setzen
        processBuilder.directory(new File("C:\\Users\\harrerm\\IdeaProjects\\DartAutoscoring\\camera"));
        processBuilder.redirectErrorStream(true);

        System.out.println("Starte Python-Skript...");
        Process process = processBuilder.start();

        // Separate Threads für Ein- und Ausgabe
        Thread outputThread = new Thread(() -> {
            try (BufferedReader reader = new BufferedReader(
                    new InputStreamReader(process.getInputStream(), StandardCharsets.UTF_8))) {
                String line;
                while ((line = reader.readLine()) != null) {
                    System.out.println("Python-Ausgabe: " + line);
                }
            } catch (IOException e) {
                e.printStackTrace();
            }
        });
        outputThread.start();

        try (BufferedWriter writer = new BufferedWriter(
                new OutputStreamWriter(process.getOutputStream()))) {
            writer.write("start");
            writer.newLine();
            writer.flush();
        }

        int exitCode = process.waitFor();
        System.out.println("Python-Skript beendet mit Code: " + exitCode);
        if (exitCode != 0) {
            System.err.println("Python-Skript wurde mit Fehlercode beendet: " + exitCode);
        }

    } catch (IOException | InterruptedException e) {
        System.err.println("Fehler beim Ausführen des Python-Skripts: " + e.getMessage());
        e.printStackTrace();
    }
}






}
