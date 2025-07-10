package com.example.model;

import lombok.AllArgsConstructor;
import lombok.Getter;

@AllArgsConstructor
@Getter
public class MatchMode {

    private final MatchModeType type;
    private final StartMode startMode;
    private final EndMode endMode;


}
