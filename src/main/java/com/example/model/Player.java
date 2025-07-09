package com.example.model;

import lombok.Getter;

import java.util.UUID;

@Getter
public class Player {

    private final UUID id;
    private final String name;

    public Player(String name) {
        this.id = UUID.randomUUID();
        this.name = name;
    }

}
