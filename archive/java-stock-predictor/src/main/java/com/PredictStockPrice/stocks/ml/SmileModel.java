package com.PredictStockPrice.stocks.ml;

import smile.classification.LogisticRegression;
import smile.data.DataFrame;
import smile.data.vector.DoubleVector;
import smile.data.vector.IntVector;

public class SmileModel {

    private LogisticRegression model;

    public void fit(double[][] X, int[] y) {
        // Smile works best with DataFrames; create one.
        var n = X.length;
        var p = n == 0 ? 0 : X[0].length;
        if (n == 0) {
            model = null;
            return;
        }

        DoubleVector[] cols = new DoubleVector[p];
        for (int j = 0; j < p; j++) {
            double[] col = new double[n];
            for (int i = 0; i < n; i++) {
                col[i] = X[i][j];
            }
            cols[j] = new DoubleVector("x" + j, col);
        }
        var df = new DataFrame(cols);

        DataFrame yDataFrame = new DataFrame(new IntVector("y", y));
        df.merge(yDataFrame);
        double[][] x = df.drop("y").toArray();
        model = LogisticRegression.fit(x, y);
    }

    public double predictProba(double[] features) {
        if (model == null) {
            return 0.5; // unknown
        }    
        // 1. Create an empty array to hold the probabilities (size 2 for UP/DOWN)
        double[] probs = new double[2];

        // 2. Call predict(). It will fill the 'probs' array with the results.
        model.predict(features, probs);
        return probs[1]; // class 1 = UP
    }
}
