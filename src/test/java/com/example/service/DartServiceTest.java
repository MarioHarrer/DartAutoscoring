package com.example.service;

import com.example.model.Player;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.util.List;
import java.util.Map;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;

class DartServiceTest {
    private DartService dartService;

    @BeforeEach
    void setup() {
        dartService = new DartService();
    }

    @Test
    void testAddPlayerAddsPlayerToList() {
        // GIVEN
        String playerName = "Testspieler";

        // WHEN
        dartService.addPlayer(playerName);

        // THEN
        List<Player> players = dartService.getPlayers();
        assertEquals(1, players.size(), "Es sollte genau ein Spieler vorhanden sein.");
        Player player = players.getFirst();
        assertEquals(playerName, player.getName(), "Der Spielername sollte korrekt sein.");
        assertNotNull(player.getId(), "Die Spieler-ID sollte generiert sein.");
    }

    @Test
    void testGetPlayerMapReturnsCorrectMapping() {
        // GIVEN
        dartService.addPlayer("Alice");
        dartService.addPlayer("Bob");
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
        dartService.addPlayer("Alice");
        dartService.addPlayer("Bob");
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
        assertEquals(1, dartService.getPlayers().size(), "Nur ein Spieler sollte vorhanden sein.");
    }

}