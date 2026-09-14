package com.PredictStockPrice.stocks.web;

import com.PredictStockPrice.stocks.dto.PredictionRequest;
import com.PredictStockPrice.stocks.model.Prediction;
import com.PredictStockPrice.stocks.service.PredictionService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1")
@RequiredArgsConstructor
public class PredictionController {
  private final PredictionService predictionService;

  @PostMapping("/predict")
  public Prediction predict(@Valid @RequestBody PredictionRequest req) {
    return predictionService.predict(req.symbol(), req.horizon());
  }
}