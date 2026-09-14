package com.PredictStockPrice.stocks.schedule;

import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import com.PredictStockPrice.stocks.service.PredictionService;

import lombok.RequiredArgsConstructor;

@Component
@RequiredArgsConstructor
public class ModelScheduler {
  private final PredictionService predictionService;

  // Retrain popular symbols daily at 8:05am UTC
  @Scheduled(cron = "0 5 8 * * *", zone = "UTC")
  public void retrain() {
    for (String s : new String[]{"AAPL","MSFT","NVDA","SPY"}) {
      try { predictionService.train(s); } catch (Exception ignored) {}
    }
  }
}
