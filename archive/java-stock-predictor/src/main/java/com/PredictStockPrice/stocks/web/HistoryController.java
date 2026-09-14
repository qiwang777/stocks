package com.PredictStockPrice.stocks.web;

import com.PredictStockPrice.stocks.data.MarketDataClient;
import com.PredictStockPrice.stocks.dto.HistoryResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1")
@RequiredArgsConstructor
public class HistoryController {

    private final MarketDataClient marketDataClient;

    @GetMapping("/history")
    public HistoryResponse history(@RequestParam String symbol, @RequestParam(defaultValue = "3mo") String range) {
        return marketDataClient.getDailyHistory(symbol, range);
    }
}
