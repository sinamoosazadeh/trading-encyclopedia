import re
from config import CATEGORIES

# Stop words - not useful for matching
STOP = {
    "a","an","the","of","in","on","at","to","for","and","or","by","with",
    "from","as","is","are","was","were","be","been","its","this","that",
    "via","per","vs","using","based","driven","toward","towards","under",
    "over","across","between","among","within","without","through","model",
    "models","method","methods","approach","framework","analysis","study",
    "evidence","theory","literature","survey","review","overview","approach",
}

# Words that are VERY specific and meaningful (always match as single word)
STRONG_SINGLES = {
    "markowitz","sharpe","sortino","calmar","kelly","vwap","twap",
    "garch","egarch","gjr","figarch","arima","sarima","arfima","var","vecm",
    "lstm","gru","cnn","rnn","tcn","transformer","autoformer","informer",
    "hawkes","ornstein","uhlenbeck","vasicek","heston","sabr","dupire",
    "almgren","chriss","avellaneda","stoikov","almgren",
    "wyckoff","ichimoku","tenkan","kijun","senkou","chikou","kumo",
    "renko","heikin","kagi","footprint","bookmap",
    "mcmc","kalman","hmm","viterbi","baum",
    "copula","archimedean","clayton","gumbel","frank",
    "capm","apt","barra","fama","french","carhart",
    "cointegration","johansen","engle","granger",
    "vpin","pin","ofi","nbbo","itch","ouch","fpga","dpdk","rdma",
    "defi","amm","mev","flashbots","uniswap","curve",
    "bitcoin","ethereum","perpetual","stablecoin",
    "tpo","vpoc","hvn","lvn","fvg","bos","choch","ipda",
    "ict","smc","wyckoff","vsa",
    "backtest","backtesting","backtested","walk-forward","wfo","cpcv","pbo",
    "monte","brownian","wiener","poisson","levy","ito",
    "drawdown","expectancy","slippage",
    "crossref","openalex",
}

# Phrases that must match as a unit (2-3 words)
STRONG_PHRASES = {
    "monte carlo", "brownian motion", "ornstein uhlenbeck",
    "mean variance", "risk parity", "value at risk", "expected shortfall",
    "order book", "limit order", "market impact", "order flow",
    "high frequency", "market making", "smart order",
    "deep learning", "machine learning", "reinforcement learning",
    "neural network", "random forest", "gradient boost",
    "time series", "point process", "stochastic volatility",
    "market profile", "volume profile", "point of control",
    "fair value", "order block", "break of structure",
    "kelly criterion", "optimal f",
    "statistical arbitrage", "pairs trading",
    "black scholes", "black litterman",
    "sharp ratio", "sharpe ratio", "information ratio",
    "regime switch", "change point", "hidden markov",
    "sentiment analysis", "natural language", "text mining",
    "price action", "chart pattern", "candlestick",
    "heikin ashi", "point figure", "three line break",
    "market microstructure", "bid ask", "adverse selection",
    "cointegration test", "unit root", "augmented dickey",
    "portfolio optimization", "mean variance", "efficient frontier",
}

def _extract_terms(kw):
    """Extract matchable terms from a keyword phrase."""
    words = re.sub(r'[^\w\s-]', ' ', kw.lower()).split()
    words = [w.strip('-') for w in words if len(w) > 2 and w.strip('-') not in STOP]

    terms = set()

    # Add strong single words
    for w in words:
        if w in STRONG_SINGLES or len(w) >= 7:
            terms.add(w)

    # Add strong 2-word phrases
    for i in range(len(words)-1):
        phrase = words[i] + ' ' + words[i+1]
        if phrase in STRONG_PHRASES:
            terms.add(phrase)
        # Also add if both words are long/meaningful
        if (len(words[i]) >= 5 and len(words[i+1]) >= 5 and
            words[i] not in STOP and words[i+1] not in STOP):
            terms.add(phrase)

    # For short keywords (1-2 meaningful words), add all words
    meaningful = [w for w in words if len(w) >= 4 and w not in STOP]
    if len(meaningful) <= 2:
        for w in meaningful:
            terms.add(w)

    return terms

def _make_pattern(term):
    """Convert term to regex pattern with British/American flexibility."""
    esc = re.escape(term)
    esc = re.sub(r'\\ ', r'[\\s_\\-]+', esc)
    esc = esc.replace('ize', 'i[sz]e').replace('ise', 'i[sz]e')
    esc = esc.replace('ization', 'i[sz]ation').replace('isation', 'i[sz]ation')
    return re.compile(r'(?<![a-z])' + esc + r'(?![a-z])', re.IGNORECASE)

def _build_patterns(categories):
    """Build: {cat: [(term, pattern), ...]}"""
    result = {}
    for cat, kws in categories.items():
        term_pats = []
        seen_terms = set()
        for kw in kws:
            for term in _extract_terms(kw):
                if term not in seen_terms:
                    seen_terms.add(term)
                    try:
                        pat = _make_pattern(term)
                        term_pats.append((term, pat))
                    except re.error:
                        pass
        result[cat] = term_pats
    return result

INFORMAL_PATTERNS = {
    "A01_Optimization": [
        r"\boptimi[sz]", r"\bcalibrat", r"\btuning\b", r"\btuned\b",
        r"\bpso\b", r"\bcma\b", r"\baco\b", r"\bsgd\b", r"\bbfgs\b",
        r"\bgenetic algorithm\b", r"\bevolutionary\b",
        r"\bnelder.?mead\b", r"\bpowell\b", r"\bquasi.?newton\b",
        r"\bhyperparameter\b", r"\bparameter search\b",
        r"\bgrid search\b", r"\brandom search\b",
    ],
    "A02_Simulation": [
        r"\bsimulat", r"\bmonte.?carlo\b", r"\bstochastic simulat",
        r"\bsynthetic data\b", r"\bscenario generat",
        r"\bsynthetic market\b", r"\bagent.based\b",
        r"\bmarkov chain.?mont", r"\bmcmc\b",
    ],
    "A03_Prediction_Forecasting": [
        r"\bforecast", r"\bpredict", r"\blstm\b", r"\bgru\b",
        r"\barima\b", r"\bsarima\b", r"\bgarch\b", r"\begarch\b",
        r"\bwavelet\b", r"\bfourier\b", r"\bfft\b", r"\bemd\b",
        r"\bhmm\b", r"\bkalman\b", r"\bhar\b",
    ],
    "A04_Backtesting_Validation": [
        r"\bbacktest", r"\bback.test", r"\bwalk.forward\b",
        r"\bout.of.sample\b", r"\bin.sample\b", r"\bwfo\b",
        r"\bvalidat", r"\bhistorical test", r"\bbar replay\b",
        r"\bstrategy test", r"\bequity curve\b",
        r"\bsharpe ratio\b", r"\bdrawdown\b", r"\bprofit factor\b",
        r"\bwin rate\b", r"\bmax drawdown\b", r"\bcalmar\b",
        r"\bsortino\b", r"\bomega ratio\b", r"\binformation ratio\b",
        r"\bdeflated sharpe\b", r"\bpbo\b", r"\bcpcv\b",
    ],
    "A05_Probability_Statistics_Econometrics": [
        r"\bstatistic", r"\bprobabilit", r"\bdistribution\b",
        r"\bcointegrat", r"\bunit root\b", r"\badf\b",
        r"\bgarch\b", r"\bcopula\b", r"\bextreme value\b",
        r"\bbayesian\b", r"\bregression\b", r"\bbootstrap\b",
        r"\bpca\b", r"\bvar\b", r"\bcvar\b",
    ],
    "B01_Machine_Learning_Finance": [
        r"\bmachine learning\b", r"\bdeep learning\b",
        r"\brandom forest\b", r"\bxgboost\b", r"\blightgbm\b",
        r"\bneural network\b", r"\bgradient boost",
        r"\bregulariz", r"\bfeature select", r"\bshap\b",
        r"\bcross.validat", r"\bensemble\b",
    ],
    "B02_Deep_Learning_Neural_Networks": [
        r"\blstm\b", r"\bgru\b", r"\bcnn\b", r"\btransformer\b",
        r"\battention mechanism\b", r"\bgraph neural\b",
        r"\bgnn\b", r"\bgcn\b", r"\bgat\b", r"\btcn\b",
        r"\bautoencoder\b", r"\bvae\b", r"\bgan\b",
        r"\bdeeplob\b", r"\brecurrent neural\b",
    ],
    "B03_Reinforcement_Learning_Control": [
        r"\breinforcement learning\b", r"\bdqn\b", r"\bppo\b",
        r"\bddpg\b", r"\bsac\b", r"\bmarkov decision\b",
        r"\bmdp\b", r"\boptimal control\b", r"\bhjb\b",
        r"\bq.learning\b", r"\bactor.critic\b",
    ],
    "B04_NLP_Sentiment_Alternative_Data": [
        r"\bsentiment\b", r"\bnlp\b", r"\btext mining\b",
        r"\bbert\b", r"\bfinbert\b", r"\bgpt\b",
        r"\balternative data\b", r"\bearnings call\b",
        r"\bnews analytic", r"\bsocial media\b",
        r"\bsatellite\b", r"\bweb scrap",
    ],
    "C01_Market_Microstructure_LOB": [
        r"\blimit order book\b", r"\blob\b", r"\bmarket microstructure\b",
        r"\border book\b", r"\bbid.ask\b", r"\bmarket depth\b",
        r"\bhawkes process\b", r"\bnbbo\b", r"\bitch\b",
        r"\bqueue\b", r"\btick size\b", r"\bprice discovery\b",
    ],
    "C02_Liquidity_OrderFlow_Informed": [
        r"\bliquidit", r"\border flow\b", r"\bvpin\b",
        r"\binformed trad", r"\badverse selection\b",
        r"\bkyle.s lambda\b", r"\bkyle lambda\b",
        r"\bpin model\b", r"\bamihud\b", r"\bflow toxic",
    ],
    "C03_Market_Impact_Execution": [
        r"\bmarket impact\b", r"\bexecution\b",
        r"\bimplementation shortfall\b", r"\balmgren\b",
        r"\bvwap\b", r"\btwap\b", r"\btransaction cost\b",
        r"\btca\b", r"\boptimal liquidat",
    ],
    "C04_HFT_MarketMaking": [
        r"\bhigh.frequency\b", r"\bhft\b", r"\bmarket making\b",
        r"\bavellaneda\b", r"\bstoikov\b",
        r"\bco.?locat", r"\bfpga\b", r"\blatency\b",
        r"\blow.latency\b", r"\bnanosecond\b",
    ],
    "C05_Algorithmic_Systematic_Trading": [
        r"\balgorithmic trad", r"\bsmart order\b",
        r"\bsystematic trad", r"\btrend following\b",
        r"\bmanaged futures\b",
    ],
    "C06_Trade_Lifecycle_Clearing": [
        r"\bclearing\b", r"\bsettlement\b", r"\bccp\b",
        r"\bmargin call\b", r"\bcentral counterpart",
        r"\bpost.trade\b", r"\bnetting\b",
    ],
    "C07_Market_Participation_Modes": [
        r"\bmargin trading\b", r"\bcfd\b", r"\bspread betting\b",
        r"\bperpetual swap\b", r"\bfunding rate\b",
        r"\bprop firm\b", r"\bfunded account\b",
        r"\bcopy trading\b", r"\bpamm\b",
    ],
    "D01_Portfolio_Construction_Optimization": [
        r"\bportfolio optim", r"\bmarkowitz\b",
        r"\befficient frontier\b", r"\bblack.litterman\b",
        r"\brisk parity\b", r"\bhierarchical risk\b",
        r"\bhrp\b", r"\bminimum variance\b",
        r"\bmaximum diversif",
    ],
    "D02_Covariance_Factor_Models": [
        r"\bcovariance\b", r"\bledoit\b", r"\bwolf\b",
        r"\brandom matrix\b", r"\bshrinkage\b",
        r"\bfactor model\b", r"\bbarra\b",
        r"\bcapm\b", r"\bfama.french\b", r"\bcarhart\b",
    ],
    "D03_Risk_Management_Tail_Stress": [
        r"\brisk manag", r"\btail risk\b", r"\bstress test",
        r"\bvar\b", r"\bcvar\b", r"\bexpected shortfall\b",
        r"\bdrawdown\b", r"\bextreme value\b",
        r"\bcoherent risk\b", r"\bsystemic risk\b",
    ],
    "D04_Position_Sizing_Kelly_Capital": [
        r"\bkelly criterion\b", r"\bkelly\b",
        r"\bposition siz", r"\bcapital allocat",
        r"\boptimal f\b", r"\bfractional kelly\b",
        r"\brisk siz", r"\bmoney manag",
        r"\bbet siz",
    ],
    "D05_Factor_Investing_Alpha_Anomalies": [
        r"\bmomentum\b", r"\bvalue factor\b", r"\bcarry\b",
        r"\bquality factor\b", r"\banomal", r"\bfactor invest",
        r"\balpha\b", r"\bbetting against beta\b",
        r"\bstatistical arbitrage\b", r"\bpairs trading\b",
        r"\bfactor zoo\b",
    ],
    "D06_Performance_Measurement_Attribution": [
        r"\bperformance attribution\b", r"\bbrinson\b",
        r"\bsharpe ratio\b", r"\binformation ratio\b",
        r"\bgips\b", r"\btime.weighted\b", r"\btwrr\b",
        r"\bperformance measur", r"\bbenchmark\b",
        r"\block versus skill\b",
    ],
    "D07_Trading_Journal_Development": [
        r"\btrading journal\b", r"\btrading plan\b",
        r"\br.multiple\b", r"\bexpectancy\b",
        r"\btrade manag", r"\btrailing stop\b",
        r"\bbreakeven\b", r"\bscaling out\b",
        r"\bposition manag",
    ],
    "E01_Derivatives_Options_Volatility": [
        r"\boption pric", r"\bblack.scholes\b", r"\bgreeks\b",
        r"\bheston model\b", r"\bsabr model\b",
        r"\bimplied volatil", r"\bvolatility surface\b",
        r"\bdelta hedge", r"\bgamma\b", r"\bvega\b",
        r"\bderivative\b",
    ],
    "E02_Fixed_Income_Rates_Credit": [
        r"\bfixed income\b", r"\binterest rate\b",
        r"\byield curve\b", r"\bvasicek\b", r"\bhull.white\b",
        r"\bcredit default\b", r"\bcds\b", r"\bbond\b",
        r"\bduration\b", r"\bcredit risk\b",
    ],
    "E03_Forex_Commodities_CrossAsset": [
        r"\bforex\b", r"\bfx\b", r"\bcurrency\b",
        r"\bcarry trade\b", r"\bcommodit", r"\bcrude oil\b",
        r"\bgold\b", r"\bcontango\b", r"\bbackwardation\b",
        r"\bintermarket\b",
    ],
    "E04_Stochastic_Calculus_MathFinance": [
        r"\bstochastic calculus\b", r"\bito.?s lemma\b",
        r"\bbownian motion\b", r"\bwiener process\b",
        r"\bgirsanov\b", r"\bmartingale\b",
        r"\bsde\b", r"\bfokker.planck\b",
        r"\bfeynman.kac\b", r"\bmalliavin\b",
    ],
    "E05_Statistical_Arbitrage_RelativeValue": [
        r"\bstatistical arbitrage\b", r"\bpairs trading\b",
        r"\bcointegrat", r"\bornstein.uhlenbeck\b",
        r"\bspread trading\b", r"\brelative value\b",
        r"\bmean reversion\b", r"\bhalf.life\b",
    ],
    "F01_MarketProfile_AuctionTheory": [
        r"\bmarket profile\b", r"\btpo\b", r"\btime price opportunit",
        r"\bvalue area\b", r"\bpoint of control\b", r"\bpoc\b",
        r"\binitial balance\b", r"\bauction market\b",
        r"\bvpoc\b", r"\bhvn\b", r"\blvn\b",
    ],
    "F02_OrderFlow_Footprint_Tape": [
        r"\bfootprint\b", r"\bcumulative delta\b", r"\bcvd\b",
        r"\btape reading\b", r"\bdom\b", r"\bdepth of market\b",
        r"\babsorption\b", r"\bimbalance\b",
        r"\bbid.ask footprint\b", r"\bstacked imbalance\b",
    ],
    "F03_Wyckoff_VSA": [
        r"\bwyckoff\b", r"\bvolume spread\b", r"\bvsa\b",
        r"\baccumulat", r"\bdistribution\b",
        r"\bselling climax\b", r"\bspring\b",
        r"\bno demand\b", r"\bno supply\b",
        r"\bsign of strength\b",
    ],
    "F04_SmartMoney_ICT": [
        r"\bsmart money\b", r"\bsmc\b", r"\bict\b",
        r"\bfair value gap\b", r"\bfvg\b",
        r"\border block\b", r"\bbreak of structure\b",
        r"\bchange of character\b", r"\bchoch\b",
        r"\bliquidity sweep\b", r"\bipda\b",
        r"\bjudas swing\b", r"\bkillzone\b",
    ],
    "F05_Technical_Analysis_ChartPatterns": [
        r"\btechnical analysis\b", r"\bchart pattern\b",
        r"\bhead and shoulder\b", r"\bdouble top\b",
        r"\btriangle pattern\b", r"\bsupport resistance\b",
        r"\bprice action\b", r"\bcandlestick\b",
        r"\bal brooks\b", r"\bbreakout\b",
    ],
    "F06_Harmonic_ElliottWave": [
        r"\bharmonic pattern\b", r"\bgartley\b", r"\bbat pattern\b",
        r"\bbutterfly pattern\b", r"\bcrab pattern\b",
        r"\belliott wave\b", r"\bfibonacci\b",
        r"\bimpulse wave\b", r"\bcorrective wave\b",
        r"\bneowave\b",
    ],
    "F07_Specialized_Trading_Schools": [
        r"\bgann\b", r"\bichimoku\b", r"\bhosoda\b",
        r"\bread the market\b", r"\brtm\b",
        r"\bbill williams\b", r"\balligator\b",
        r"\bjoe ross\b", r"\bross hook\b",
        r"\bkagi\b", r"\bthree line break\b",
    ],
    "F08_EventDriven_News_Trading": [
        r"\bearnings announcement\b", r"\bfomc\b",
        r"\bnon.farm payroll\b", r"\bnfp\b",
        r"\bevent.driven\b", r"\bnews trading\b",
        r"\bvolatility crush\b", r"\bearnings surprise\b",
        r"\bindex rebalanc", r"\bm.?a\b",
    ],
    "F09_Trading_Styles_Timeframes": [
        r"\bscalping\b", r"\bday trading\b", r"\bintraday\b",
        r"\bswing trading\b", r"\bposition trading\b",
        r"\bbuy and hold\b", r"\bvalue invest",
        r"\bdollar cost averag", r"\bmulti.timeframe\b",
        r"\btrend following\b",
    ],
    "F10_Chart_Types_Visualization": [
        r"\bcandlestick chart\b", r"\brenko\b",
        r"\bheikin.?ashi\b", r"\bpoint and figure\b",
        r"\bkagi chart\b", r"\bthree line break\b",
        r"\brange bar\b", r"\btick chart\b",
        r"\blogarithmic scale\b", r"\blinear scale\b",
        r"\bvolume profile\b",
    ],
    "F11_Market_Scanning_Screening": [
        r"\bstock screener\b", r"\bmarket scanner\b",
        r"\brelative strength\b", r"\bvolume surge\b",
        r"\bgolden cross\b", r"\bdeath cross\b",
        r"\bmarket breadth\b", r"\bunusual option\b",
        r"\badvance.decline\b",
    ],
    "G01_Fundamental_Analysis_Valuation": [
        r"\bdiscounted cash flow\b", r"\bdcf\b",
        r"\bwacc\b", r"\benterpr", r"\bvaluat",
        r"\bprice.to.earnings\b", r"\bp\/e ratio\b",
        r"\baltman\b", r"\bbeneish\b", r"\bdupont\b",
        r"\bfundamental analysis\b",
    ],
    "G02_Macro_Intermarket_CentralBanking": [
        r"\bmonetary policy\b", r"\bquantitative easing\b",
        r"\byield curve\b", r"\binflation\b",
        r"\bfed funds\b", r"\bcentral bank\b",
        r"\bnon.farm payroll\b", r"\bintermarket\b",
        r"\bbusiness cycle\b", r"\bsector rotation\b",
    ],
    "G03_Behavioral_Finance_Decision": [
        r"\bbehavioral finance\b", r"\bprospect theory\b",
        r"\bloss aversion\b", r"\bdisposition effect\b",
        r"\boverconfidence\b", r"\banchoring\b",
        r"\bherding\b", r"\blimits of arbitrage\b",
        r"\bnoise trader\b",
    ],
    "H01_Crypto_DeFi_OnChain": [
        r"\bcryptocurrenc", r"\bbitcoin\b", r"\bethereum\b",
        r"\bdefi\b", r"\bdecentralized\b", r"\bamm\b",
        r"\buniswap\b", r"\bmev\b", r"\bperpetual swap\b",
        r"\bfunding rate\b", r"\bon.chain\b",
        r"\bblockchain\b",
    ],
    "H02_TradingSystems_Engineering": [
        r"\btrading system\b", r"\bevent.driven architect",
        r"\blow.latency\b", r"\bmatching engine\b",
        r"\bkdb\b", r"\bfix protocol\b",
        r"\bstream processing\b", r"\bmlops\b",
    ],
    "H03_Regulation_Compliance_Integrity": [
        r"\bregulat", r"\bcompliance\b", r"\bmifid\b",
        r"\breg nms\b", r"\bsec rule\b", r"\bcftc\b",
        r"\bmarket abuse\b", r"\bspoofing\b",
        r"\bbest execution\b",
    ],
    "H04_PropFirm_Retail_Grid": [
        r"\bprop firm\b", r"\bprop trading\b",
        r"\bfunded account\b", r"\bgrid trading\b",
        r"\bmartingale\b", r"\bzone recovery\b",
        r"\bftmo\b", r"\bdrawdown rule\b",
    ],
    "H05_MarketData_Feeds_Architecture": [
        r"\bmarket data\b", r"\bl1 data\b", r"\bl2 data\b",
        r"\bl3 data\b", r"\bnbbo\b", r"\border book feed\b",
        r"\bdirect feed\b", r"\bconsolidat", r"\bitch\b",
        r"\btick data\b", r"\bohlcv\b",
    ],
    "H06_Exchange_Connectivity_API_OMS": [
        r"\brest api\b", r"\bwebsocket\b", r"\bfix protocol\b",
        r"\bapi connect", r"\border manag", r"\boms\b",
        r"\bpre.trade risk\b", r"\bhmac\b",
    ],
    "H07_Network_Infrastructure_DataCenters": [
        r"\bco.?locat", r"\bdata center\b", r"\bequinix\b",
        r"\bmicrowave\b", r"\bfiber optic\b",
        r"\blatency\b", r"\bptp\b", r"\bieee 1588\b",
        r"\bhardware timestamp\b",
    ],
    "H08_Trading_Platforms_Tools": [
        r"\bmetatrader\b", r"\bmt4\b", r"\bmt5\b",
        r"\btradingview\b", r"\bpine script\b",
        r"\bquantconnect\b", r"\bbacktrader\b",
        r"\bvectorbt\b", r"\bninjascript\b",
        r"\bjupyter\b",
    ],
}

def _compile_informal():
    result = {}
    for cat, patterns in INFORMAL_PATTERNS.items():
        compiled = []
        for p in patterns:
            try:
                compiled.append(re.compile(p, re.IGNORECASE))
            except re.error:
                pass
        result[cat] = compiled
    return result

_INF_COMPILED = _compile_informal()

# Classification is based on document evidence, never on the search bucket alone.
# These terms establish a finance/trading context; "market" by itself is intentionally
# excluded because it is common in unrelated disciplines.
_FINANCE_CONTEXT = re.compile(
    r"\b(?:finance|financial|trading|trader|stock market|stock returns|equity returns|"
    r"investment|investing|portfolio|quantitative finance|systematic trading|"
    r"algorithmic trading|financial market|market microstructure|market making|"
    r"order book|market data|derivative|futures market|options market|forex|"
    r"foreign exchange|cryptocurrency|bitcoin|ethereum|crypto assets?|risk management|"
    r"asset pricing|asset allocation|capital market|financial econom\w*|"
    r"transaction cost|execution cost|trade execution|trading strateg\w*|"
    r"price discovery|financial time series|financial econometrics|volatility|"
    r"stock price|asset returns?|financial data|electronic trading|trading system|"
    r"fixed income|bond market|currency market|perpetual swap|funding rate)\b",
    re.IGNORECASE,
)

# A few specialized concepts are sufficiently domain-specific to stand on their own.
# Ambiguous abbreviations such as ICT, SMC, VAR, PIN, and DOM are not in this list.
_DIRECT_CATEGORY_PATTERNS = {
    "A01_Optimization": re.compile(
        r"\b(?:trading strategy optimization|portfolio optimization|kelly criterion|"
        r"optimal f position sizing|walk.forward optimization|parameter optimization trading)\b",
        re.IGNORECASE),
    "A02_Simulation": re.compile(
        r"\b(?:market microstructure simulation|order book simulation|trading simulation|"
        r"synthetic market data)\b", re.IGNORECASE),
    "A03_Prediction_Forecasting": re.compile(
        r"\b(?:stock price prediction|financial time series forecasting|"
        r"volatility forecasting|financial forecasting)\b", re.IGNORECASE),
    "A04_Backtesting_Validation": re.compile(
        r"\b(?:backtesting trading strateg\w*|walk.forward optimization|"
        r"deflated sharpe|probability of backtest overfitting|combinatorial purged cross.validation)\b",
        re.IGNORECASE),
    "A05_Probability_Statistics_Econometrics": re.compile(
        r"\b(?:financial econometrics|asset pricing|value at risk|expected shortfall|"
        r"deflated sharpe|financial time series)\b", re.IGNORECASE),
    "B01_Machine_Learning_Finance": re.compile(
        r"\b(?:machine learning in finance|financial machine learning|"
        r"ml in trading|machine learning trading strateg\w*)\b", re.IGNORECASE),
    "B02_Deep_Learning_Neural_Networks": re.compile(
        r"\b(?:deeplob|deep learning in finance|deep learning for trading|"
        r"financial time series transformer)\b", re.IGNORECASE),
    "B03_Reinforcement_Learning_Control": re.compile(
        r"\b(?:reinforcement learning for trading|reinforcement learning market making|"
        r"rl optimal execution|rl portfolio allocation)\b", re.IGNORECASE),
    "B04_NLP_Sentiment_Alternative_Data": re.compile(
        r"\b(?:financial sentiment analysis|finbert|financial news sentiment|"
        r"sentiment analysis stock market)\b", re.IGNORECASE),
    "C01_Market_Microstructure_LOB": re.compile(
        r"\b(?:limit order book|market microstructure|order book reconstruction|"
        r"order book imbalance|price discovery)\b", re.IGNORECASE),
    "C02_Liquidity_OrderFlow_Informed": re.compile(
        r"\b(?:order flow|liquidity sweep|probability of informed trading|"
        r"volume.synchronized probability of informed trading|kyle.?s lambda)\b",
        re.IGNORECASE),
    "C03_Market_Impact_Execution": re.compile(
        r"\b(?:market impact|implementation shortfall|vwap|twap|transaction cost analysis)\b",
        re.IGNORECASE),
    "C04_HFT_MarketMaking": re.compile(
        r"\b(?:high.frequency trading|market making|avellaneda.stoikov|"
        r"low.latency trading)\b", re.IGNORECASE),
    "F01_MarketProfile_AuctionTheory": re.compile(
        r"\b(?:market profile|volume profile|time price opportunity|point of control)\b",
        re.IGNORECASE),
    "F02_OrderFlow_Footprint_Tape": re.compile(
        r"\b(?:order flow footprint|cumulative volume delta|tape reading|"
        r"depth of market|stacked imbalance)\b", re.IGNORECASE),
    "F03_Wyckoff_VSA": re.compile(
        r"\b(?:wyckoff|volume spread analysis|vsa trading|selling climax|"
        r"sign of strength wyckoff)\b", re.IGNORECASE),
    "F04_SmartMoney_ICT": re.compile(
        r"\b(?:smart money concepts?|fair value gap|inversion fair value gap|"
        r"balanced price range|order block|break of structure|change of character|"
        r"liquidity sweep|interbank price delivery algorithm|judas swing|killzone|"
        r"inner circle trader)\b|"
        r"\b(?:ict|smc)\b(?=.*\b(?:trading|trader|forex|futures|liquidity|"
        r"order block|fair value gap|fvg|market structure|killzone)\b)",
        re.IGNORECASE),
    "F05_Technical_Analysis_ChartPatterns": re.compile(
        r"\b(?:technical analysis|head and shoulders pattern|double top pattern|"
        r"double bottom pattern|candlestick pattern|price action trading)\b",
        re.IGNORECASE),
    "F06_Harmonic_ElliottWave": re.compile(
        r"\b(?:elliott wave|harmonic pattern|gartley pattern|bat pattern trading|"
        r"neowave|elliott corrective wave)\b", re.IGNORECASE),
    "F07_Specialized_Trading_Schools": re.compile(
        r"\b(?:ichimoku|gann trading|read the market rtm|bill williams trading|"
        r"joe ross trading)\b", re.IGNORECASE),
    "H01_Crypto_DeFi_OnChain": re.compile(
        r"\b(?:cryptocurrency|crypto trading|decentralized finance|uniswap|"
        r"on.chain trading|perpetual swap)\b", re.IGNORECASE),
    "H02_TradingSystems_Engineering": re.compile(
        r"\b(?:trading system architecture|trading systems engineering|"
        r"electronic trading system|exchange connectivity|order management system|"
        r"matching engine)\b", re.IGNORECASE),
}


def classify_with_evidence(title, source_category=None, context_text=None):
    """Return evidence-backed category assignments.

    source_category is retained for compatibility and diagnostics only. It never
    forces an assignment. The returned matched patterns are audit clues, not
    calibrated probabilities or claims of scientific validity.
    """
    title_text = str(title or "").strip()
    context = str(context_text or "").strip()
    searchable = (title_text + " " + context).strip()
    if not searchable:
        return []

    has_finance_context = bool(_FINANCE_CONTEXT.search(searchable))
    assignments = []
    for category, patterns in _INF_COMPILED.items():
        matched = []
        for pattern in patterns:
            match = pattern.search(searchable)
            if match:
                snippet = match.group(0).strip()
                if snippet and snippet.casefold() not in {x.casefold() for x in matched}:
                    matched.append(snippet)
        if not matched:
            continue

        direct_pattern = _DIRECT_CATEGORY_PATTERNS.get(category)
        direct_evidence = bool(direct_pattern and direct_pattern.search(searchable))
        if not has_finance_context and not direct_evidence:
            continue

        assignments.append({
            "category": category,
            "matched_patterns": matched[:12],
            "finance_context_found": has_finance_context,
            "direct_domain_evidence": direct_evidence,
            "source_query_category": source_category if source_category in CATEGORIES else None,
        })

    return sorted(assignments, key=lambda row: row["category"])


def classify(title, source_category=None, context_text=None):
    """Return category IDs supported by document evidence.

    Search-bucket metadata is deliberately not a fallback classification rule.
    Documents without adequate evidence remain unclassified for later review.
    """
    return [
        row["category"]
        for row in classify_with_evidence(title, source_category, context_text)
    ]
