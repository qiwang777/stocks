package com.PredictStockPrice.stocks.model;

import java.time.Instant;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Prediction {

    public enum Move {
        UP, DOWN
    }
    private String symbol;
    private String horizon; // e.g., "1d", "30m"
    private Instant asOf;
    private double lastPrice;
    private Move predictedMove;
    private double confidence; // 0..1
    private String rationale;  // optional LLM rationale
}
