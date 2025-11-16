package com.PredictStockPrice.stocks.dto;

import jakarta.validation.constraints.NotBlank;

public record PredictionRequest(@NotBlank String symbol, @NotBlank String horizon) {}

