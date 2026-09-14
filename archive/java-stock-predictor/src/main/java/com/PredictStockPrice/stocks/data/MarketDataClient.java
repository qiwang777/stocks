package com.PredictStockPrice.stocks.data;

import java.time.Instant;
import java.time.ZoneOffset;
import java.time.format.DateTimeFormatterBuilder;
import java.time.temporal.ChronoField;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;

import com.PredictStockPrice.stocks.dto.HistoryResponse;
import com.PredictStockPrice.stocks.model.Bar;

import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Flux;

@Component
@RequiredArgsConstructor
public class MarketDataClient {

    private final WebClient webClient;

    @Value("${marketdata.provider:alphaVantage}")
    private String provider;

    @Value("${marketdata.alphaVantage.baseUrl}")
    private String avBaseUrl;
    @Value("${marketdata.alphaVantage.apiKey}")
    private String avKey;

    @Value("${marketdata.finage.baseUrl}")
    private String finBaseUrl;
    @Value("${marketdata.finage.apiKey}")
    private String finKey;

    @Cacheable("symbols")
    public HistoryResponse getDailyHistory(String symbol, String range) {
        return switch (provider.toLowerCase()) {
            case "finage" ->
                finageDaily(symbol, range);
            default ->
                alphaVantageDaily(symbol);
        };
    }

    public static Map<String, String> createDailyData(String open, String high, String low, String close, String volume) {
        Map<String, String> dailyData = new HashMap<>();
        dailyData.put("1. open", open);
        dailyData.put("2. high", high);
        dailyData.put("3. low", low);
        dailyData.put("4. close", close);
        dailyData.put("5. volume", volume);
        return dailyData;
    }
    
    /**
     * Helper method for the incomplete daily data.
     */
    public static Map<String, String> createDailyData(String open, String high) {
        Map<String, String> dailyData = new HashMap<>();
        dailyData.put("1. open", open);
        dailyData.put("2. high", high);
        return dailyData;
    }

    // Alpha Vantage daily (compact)
    private HistoryResponse alphaVantageDaily(String symbol) {

        // Map<String, Object> stockData = new HashMap<>();

        // // Add the "Meta Data" map
        // Map<String, String> metaData = new HashMap<>();
        // metaData.put("1. Information", "Daily Prices (open, high, low, close) and Volumes");
        // metaData.put("2. Symbol", "IBM");
        // metaData.put("3. Last Refreshed", "2025-10-10");
        // metaData.put("4. Output Size", "Compact");
        // metaData.put("5. Time Zone", "US/Eastern");
        // stockData.put("Meta Data", metaData);
        // Map<String, Map<String, String>> timeSeriesDaily = new HashMap<>();
        
        // timeSeriesDaily.put("2025-10-10", createDailyData("289.2500", "290.3850", "277.5300", "277.8100", "4488241"));
        // timeSeriesDaily.put("2025-10-09", createDailyData("289.8200", "290.1300", "283.3200", "288.2300", "4912375"));
        // timeSeriesDaily.put("2025-10-08", createDailyData("294.1600", "294.2000", "286.4730", "289.4600", "5297030"));
        // timeSeriesDaily.put("2025-10-07", createDailyData("295.5500", "301.0425", "293.2850", "293.8700", "7190126"));
        // timeSeriesDaily.put("2025-10-06", createDailyData("288.6100", "291.4500", "287.8000", "289.4200", "2881947"));
        // timeSeriesDaily.put("2025-10-03", createDailyData("287.5000", "293.3200", "287.3000", "288.3700", "4375082"));

        // stockData.put("Time Series (Daily)", timeSeriesDaily);



        var uri = avBaseUrl + "/query?function=TIME_SERIES_DAILY&symbol=" + symbol + "&outputsize=compact&apikey=" + avKey;
        var body = webClient.get().uri(uri).retrieve().bodyToMono(Map.class).block();
        var fmt = new DateTimeFormatterBuilder().appendPattern("yyyy-MM-dd")
                .parseDefaulting(ChronoField.HOUR_OF_DAY, 0)
                .parseDefaulting(ChronoField.MINUTE_OF_HOUR, 0)
                .parseDefaulting(ChronoField.SECOND_OF_MINUTE, 0)
                .toFormatter()
                .withZone(ZoneOffset.UTC);
        List<Bar> bars = new ArrayList<>();
        if (body == null) {
            return new HistoryResponse(symbol, "1d", bars);
        }
        Object seriesObj = body.get("Time Series (Daily)");

        if (seriesObj instanceof Map<?, ?>) {
            Map<?, ?> series = (Map<?, ?>) seriesObj;
            series.forEach((dateObj, ohlcObj) -> {
                if (!(dateObj instanceof String) || !(ohlcObj instanceof Map<?, ?>)) {
                    return;
                }
                String date = (String) dateObj;
                Map<?, ?> mAny = (Map<?, ?>) ohlcObj;
                try {
                    String openS = Objects.toString(mAny.get("1. open"), null);
                    String highS = Objects.toString(mAny.get("2. high"), null);
                    String lowS = Objects.toString(mAny.get("3. low"), null);
                    String closeS = Objects.toString(mAny.get("4. close"), null);
                    String volS = Objects.toString(mAny.get("5. volume"), null);
                    if (openS == null || highS == null || lowS == null || closeS == null || volS == null) {
                        return;
                    }

                    Bar.BarBuilder bar = Bar.builder();
                    bar.time(Instant.from(fmt.parse(date)));
                    bar.open(Double.parseDouble(openS));
                    bar.high(Double.parseDouble(highS));
                    bar.low(Double.parseDouble(lowS));
                    bar.close(Double.parseDouble(closeS));
                    bar.volume(Long.parseLong(volS));

                    bars.add(bar.build());
                } catch (Exception e) {
                    // skip malformed entries
                }
            });
            bars.sort(Comparator.comparing(Bar::getTime));
        }
        return new HistoryResponse(symbol, "1d", bars);
    }
    
    // Finage placeholder (adjust per your plan)
    private HistoryResponse finageDaily(String symbol, String range) {
        // Example endpoint (adjust plan/params): /agg/stock/ticker?symbol=AAPL&resolution=1D&from=...&to=...&apikey=...
        return new HistoryResponse(symbol, "1d", List.of());
    }

    // Simple realtime stream mock using polling + SSE
    public Flux<String> streamPrices(String symbol) {
        // Replace with websocket provider or Finage socket if available.
        return Flux.interval(java.time.Duration.ofSeconds(3))
                .flatMap(tick -> webClient.get()
                .uri(avBaseUrl + "/query?function=GLOBAL_QUOTE&symbol=" + symbol + "&apikey=" + avKey)
                .accept(MediaType.APPLICATION_JSON)
                .retrieve()
                .bodyToMono(Map.class)
                .map(map -> {
                    Map<String, String> q = (Map<String, String>) map.get("Global Quote");
                    return q != null ? q.get("05. price") : null;
                }))
                .filter(Objects::nonNull);
    }
}
