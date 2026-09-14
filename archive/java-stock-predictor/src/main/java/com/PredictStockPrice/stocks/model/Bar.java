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
public class Bar {

    private Instant time;
    private double open;
    private double high;
    private double low;
    private double close;
    private long volume;
}
