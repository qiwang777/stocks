package com.PredictStockPrice.stocks.dto;

import com.PredictStockPrice.stocks.model.Bar;
import java.util.List;

public record HistoryResponse(String symbol, String interval, List<Bar> bars) {}