package com.PredictStockPrice.stocks.service;

import java.util.List;

import org.springframework.ai.chat.client.ChatClient;
import org.springframework.stereotype.Service;

import com.PredictStockPrice.stocks.model.Bar;
import com.PredictStockPrice.stocks.model.Prediction;

import lombok.RequiredArgsConstructor;

@Service
@RequiredArgsConstructor
public class RationaleService {

    private final ChatClient chatClient;

    public String explain(String symbol, String horizon, double pUp, Prediction.Move move, List<Bar> recent) {
        try {
            var prompt = "You are a concise market commentary assistant. Given an ML probability (" + pUp + ") that next move for " + symbol + " over horizon " + horizon + " is " + move + ", generate a two-sentence neutral rationale based on generic technical signals (SMA/RSI/volatility). Do not provide financial advice.";
            return chatClient.prompt().user(prompt).call().content();
        } catch (Exception e) {
            return "Rationale unavailable.";
        }
    }
}
