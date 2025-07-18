package com.example.service;

import com.example.model.*;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.util.List;
import java.util.Map;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;

class DartServiceTest {
    private DartService dartService;
    private MatchMode matchmode;
    private MatchModeType matchmodetype;

    @BeforeEach
    void setup() {
        dartService = new DartService();
        dartService.addPlayer("Alice");
        dartService.addPlayer("Bob");
        matchmodetype = MatchModeType.MODE_501;
        matchmode = new MatchMode(matchmodetype, StartMode.STRAIGHT_IN, EndMode.STRAIGHT_OUT);
    }

    @Test
    void testAddPlayerAddsPlayerToList() {
        // GIVEN
        String playerName = "Testspieler";

        // WHEN
        dartService.addPlayer(playerName);

        // THEN
        List<Player> players = dartService.getPlayers();
        assertEquals(3, players.size(), "Es sollte genau ein Spieler vorhanden sein.");
        Player player = players.getFirst();
        assertEquals("Alice", player.getName(), "Der Spielername sollte korrekt sein.");
        assertNotNull(player.getId(), "Die Spieler-ID sollte generiert sein.");
    }

    @Test
    void testGetPlayerMapReturnsCorrectMapping() {
        // GIVEN
        List<Player> players = dartService.getPlayers();

        // WHEN
        Map<UUID, Player> playerMap = dartService.getPlayerMap();

        // THEN
        assertEquals(players.size(), playerMap.size(), "Die Map sollte die gleiche Anzahl an Spielern enthalten wie die Liste.");
        for (Player p : players) {
            assertTrue(playerMap.containsKey(p.getId()), "Die Map sollte die Spieler-ID enthalten.");
            assertEquals(p, playerMap.get(p.getId()), "Die Map sollte den Spieler korrekt abbilden.");
        }
    }

    @Test
    void testResetPlayersClearsPlayerList() {
        // GIVEN
        assertEquals(2, dartService.getPlayers().size(), "Setup-Check: Zwei Spieler sollten vorhanden sein.");

        // WHEN
        dartService.resetPlayers(); // << Diese Methode existiert NOCH NICHT


        // THEN
        assertTrue(dartService.getPlayers().isEmpty(), "Nach dem Reset sollte die Liste leer sein.");
    }

    @Test
    void testAddPlayerReturnsFalseIfNameExists() {
        boolean first = dartService.addPlayer("Anna");
        boolean second = dartService.addPlayer("Anna");

        assertTrue(first, "Erster Spieler sollte hinzugefügt werden.");
        assertFalse(second, "Zweiter Spieler mit gleichem Namen sollte nicht hinzugefügt werden.");
        assertEquals(3, dartService.getPlayers().size(), "Nur ein Spieler sollte vorhanden sein.");
    }

    /*@Test
    void testDeletPlayer(){
        dartService.deletePlayer("Alice");
        assertEquals(1, dartService.getPlayers().size(), "Ein Spieler soll nur vorhanden sein.");
    }*/

    @Test
    void testGetMatch(){
        dartService.startNewMatch(List.of(dartService.getPlayers().get(0).getId()), matchmode);
        assertNotNull(dartService.getMatch(), "Es sollte ein Spiel gestartet sein.");
    }

    @Test
    void testEndMatch(){
        dartService.startNewMatch(List.of(dartService.getPlayers().get(0).getId()), matchmode);
        assertNotNull(dartService.getMatch(), "Es sollte ein Spiel gestartet sein.");
        dartService.endMatch();
        assertNull(dartService.getMatch(), "Es sollte kein Spiel mehr gestartet sein.");
    }
    @Test
    void testIsValidThrow(){
        dartService.startNewMatch(List.of(dartService.getPlayers().get(0).getId()), matchmode);
        Match match = dartService.getMatch();
        GameState gamestate = match.getGameState();
        UUID playerId = dartService.getPlayers().get(0).getId();
        ThrowResult throwResult = new ThrowResult(50, false, false);

        dartService.processThrow(playerId, throwResult);
        assertEquals(451, match.getScores().get(playerId)
                , "Der aktuelle Spielscore sollte 501 sein.");

        UUID playerId2 = dartService.getPlayers().get(1).getId();
        assertThrows(IllegalArgumentException.class, () -> dartService.processThrow(playerId2, throwResult));

        gamestate.setThrowsleft(0);
        assertThrows(IllegalArgumentException.class, () -> dartService.processThrow(playerId, throwResult));

        gamestate.setGameover(true);
        assertThrows(IllegalArgumentException.class, () -> dartService.processThrow(playerId, throwResult));

    }

    @Test
    void testNextTurn(){
        List<Player> players = dartService.getPlayers();
        UUID player1Id = players.get(0).getId();
        UUID player2Id = players.get(1).getId();

        dartService.startNewMatch(List.of(player1Id, player2Id), matchmode);
        Match match = dartService.getMatch();
        GameState gameState = match.getGameState();
        ThrowResult throwResult = new ThrowResult(20, false, false);


        assertEquals(player1Id, gameState.getCurrentplayerId(), "Erster Spieler sollte beginnen");
        assertEquals(3, gameState.getThrowsleft());

        dartService.processThrow(player1Id, throwResult);
        dartService.processThrow(player1Id, throwResult);
        dartService.processThrow(player1Id, throwResult);


        assertEquals(player2Id, gameState.getCurrentplayerId());
        assertEquals(3, gameState.getThrowsleft());
        assertEquals(1, gameState.getCurrentplayerIndex(), "Spielerindex sollte auf 1 sein");
        assertEquals(441, match.getScores().get(player1Id));
        assertEquals(501, match.getScores().get(player2Id));

    }

    @Test
    void testDoubleThrow(){
        MatchMode matchmode = new MatchMode(MatchModeType.MODE_501, StartMode.DOUBLE_IN, EndMode.DOUBLE_OUT);
        dartService.startNewMatch(List.of(dartService.getPlayers().get(0).getId()), matchmode);
        UUID playerId = dartService.getPlayers().get(0).getId();
        ThrowResult throwResult = new ThrowResult(20, false, false);

        dartService.processThrow(playerId, throwResult);
        assertEquals(501, dartService.getMatch().getScores().get(playerId));
    }




}