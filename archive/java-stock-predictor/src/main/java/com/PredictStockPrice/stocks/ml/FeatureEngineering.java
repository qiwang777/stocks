package com.PredictStockPrice.stocks.ml;

import java.util.ArrayList;
import java.util.List;

import com.PredictStockPrice.stocks.model.Bar;

public class FeatureEngineering {

    /**
     * Builds a feature matrix X and label vector y for a binary classification:
     * label = 1 if next-day return > 0, else 0.
     */
    public static Dataset buildDataset(List<Bar> bars) {
        // Need at least ~20 points for features.
        if (bars.size() < 25) {
            return new Dataset(new double[0][0], new int[0]);
        }
        List<double[]> feats = new ArrayList<>();
        List<Integer> labels = new ArrayList<>();

        for (int i = 20; i < bars.size() - 1; i++) {
            double[] f = features(bars, i);
            feats.add(f);
            double today = bars.get(i).getClose();
            double next = bars.get(i + 1).getClose();
            labels.add(next > today ? 1 : 0);
        }
        double[][] X = feats.toArray(double[][]::new);
        int[] y = labels.stream().mapToInt(Integer::intValue).toArray();
        return new Dataset(X, y);
    }

    public static double[] features(List<Bar> bars, int i) {
        // Basic indicators: returns, SMA, RSI(14), volatility(10)
        double close = bars.get(i).getClose();
        double prev = bars.get(i - 1).getClose();
        double ret1 = (close - prev) / prev;

        double sma5 = sma(bars, i, 5);
        double sma10 = sma(bars, i, 10);
        double sma20 = sma(bars, i, 20);
        double rsi14 = rsi(bars, i, 14);
        double vol10 = volatility(bars, i, 10);

        return new double[]{ret1, sma5 / close, sma10 / close, sma20 / close, rsi14, vol10};
    }

    static double sma(List<Bar> bars, int i, int w) {
        double s = 0;
        for (int k = i - w + 1; k <= i; k++) {
            s += bars.get(k).getClose();
        }
        return s / w;
    }

    static double volatility(List<Bar> bars, int i, int w) {
        double m = sma(bars, i, w);
        double s2 = 0;
        for (int k = i - w + 1; k <= i; k++) {
            double d = bars.get(k).getClose() - m;
            s2 += d * d;
        }
        return Math.sqrt(s2 / w) / m; // normalized stdev
    }

    static double rsi(List<Bar> bars, int i, int period) {
        double gain = 0, loss = 0;
        for (int k = i - period + 1; k <= i; k++) {
            double diff = bars.get(k).getClose() - bars.get(k - 1).getClose();
            if (diff >= 0) {
                gain += diff;
            } else {
                loss -= diff;
            }
        }
        if (loss == 0) {
            return 1.0; // high RSI

        }
        double rs = (gain / period) / (loss / period);
        return rs / (1 + rs); // normalize to 0..1
    }

    public record Dataset(double[][] X, int[] y) {

    }
}
