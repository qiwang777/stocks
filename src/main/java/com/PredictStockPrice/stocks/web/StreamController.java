package com.PredictStockPrice.stocks.web;

import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.PredictStockPrice.stocks.data.MarketDataClient;

import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Flux;

@RestController
@RequestMapping("/api/v1/stream")
@RequiredArgsConstructor
public class StreamController {
  private final MarketDataClient marketDataClient;

  // Server-Sent Events stream of prices as plain text lines (price per tick)
  @GetMapping(value = "/quotes", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
  public Flux<String> quotes(@RequestParam String symbol) {
    return marketDataClient.streamPrices(symbol);
  }
}