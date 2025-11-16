package com.PredictStockPrice.stocks.service;

import java.time.Instant;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Service;

import com.PredictStockPrice.stocks.data.MarketDataClient;
import com.PredictStockPrice.stocks.dto.HistoryResponse;
import com.PredictStockPrice.stocks.ml.FeatureEngineering;
import com.PredictStockPrice.stocks.ml.SmileModel;
import com.PredictStockPrice.stocks.model.Prediction;

import lombok.RequiredArgsConstructor;

@Service
@RequiredArgsConstructor
public class PredictionService {

    private final MarketDataClient marketDataClient;
    private final RationaleService rationaleService; // optional, can be no-op
    private final Map<String, SmileModel> models = new ConcurrentHashMap<>();

    @Cacheable("models")
    public SmileModel train(String symbol) {
        HistoryResponse hist = marketDataClient.getDailyHistory(symbol, "3mo");
        var ds = FeatureEngineering.buildDataset(hist.bars());
        SmileModel model = new SmileModel();
        model.fit(ds.X(), ds.y());
        models.put(symbol, model);
        return model;
    }

    public Prediction predict(String symbol, String horizon) {
        var hist = marketDataClient.getDailyHistory(symbol, "3mo");
        var bars = hist.bars();
        var ds = FeatureEngineering.buildDataset(bars);
        SmileModel model = models.computeIfAbsent(symbol, s -> {
            SmileModel m = new SmileModel();
            m.fit(ds.X(), ds.y());
            return m;
        });
        if (bars.isEmpty()) {
            return Prediction.builder()
                    .symbol(symbol).horizon(horizon).asOf(Instant.now())
                    .lastPrice(0).predictedMove(Prediction.Move.UP).confidence(0.5).build();
        }

        double[] f = FeatureEngineering.features(bars, bars.size() - 1);
        double pUp = model.predictProba(f);
        var move = pUp >= 0.5 ? Prediction.Move.UP : Prediction.Move.DOWN;
        var last = bars.get(bars.size() - 1).getClose();
        String rationale = rationaleService.explain(symbol, horizon, pUp, move, bars);

        return Prediction.builder()
                .symbol(symbol)
                .horizon(horizon)
                .asOf(Instant.now())
                .lastPrice(last)
                .predictedMove(move)
                .confidence(Math.abs(pUp - 0.5) * 2) // convert to 0..1 distance
                .rationale(rationale)
                .build();
    }
}
