# Pinterest Analytics Widgets Documentation

## 🎯 Overview

The Pinterest Analytics Widgets system provides specialized analytics widgets for Pinterest performance tracking that integrate with the Track AI dashboard. These widgets offer deep insights into Pinterest campaign performance, pin analytics, audience demographics, and cross-platform attribution.

## 📊 Available Widgets

### 1. Campaign ROI Comparison Widget
**Type**: Bar Chart  
**Purpose**: Compare Pinterest campaign performance metrics including ROAS, CPA, revenue, and spend.

**Features**:
- Campaign performance ranking by ROAS
- Revenue and spend comparison
- Average ROAS calculation
- Best performing campaign identification

**Data Points**:
- Campaign ID and name
- ROAS (Return on Ad Spend)
- CPA (Cost Per Acquisition)
- Revenue and spend amounts
- Impressions, clicks, and purchases

### 2. Pin Performance Analysis Widget
**Type**: Scatter Plot  
**Purpose**: Analyze individual pin performance with CTR vs Save Rate visualization.

**Features**:
- Top performing pins identification
- CTR and save rate analysis
- Pin performance scoring
- Impression and engagement metrics

**Data Points**:
- Pin ID and campaign association
- Impressions, clicks, and saves
- CTR and save rate percentages
- Spend and revenue per pin

### 3. Audience Demographics Widget
**Type**: Pie Chart  
**Purpose**: Display Pinterest audience demographics and customer persona insights.

**Features**:
- Customer persona generation
- Age group and gender distribution
- Interest categorization
- Behavioral pattern analysis

**Data Points**:
- Persona name and generation timestamp
- Age groups and gender distribution
- Interest categories
- Engagement patterns

### 4. Purchase Funnel Visualization Widget
**Type**: Funnel Chart  
**Purpose**: Track Pinterest-to-purchase conversion funnel with stage-by-stage analysis.

**Features**:
- Multi-stage funnel visualization
- Conversion rate calculation
- Funnel efficiency metrics
- Stage-by-stage performance

**Data Points**:
- Impressions → Clicks → Saves → Website Clicks → Purchases
- Conversion rates between stages
- Overall funnel efficiency
- Total impressions and purchases

### 5. Discovery Phase Metrics Widget
**Type**: Line Chart  
**Purpose**: Analyze Pinterest discovery phase performance with impression, save, closeup, and click metrics.

**Features**:
- Discovery phase scoring
- Impression and engagement analysis
- Save and closeup rate tracking
- Overall discovery score calculation

**Data Points**:
- Impressions, saves, closeups, clicks
- Save rate, closeup rate, click rate
- Discovery phase scores
- Overall discovery performance

### 6. Trend Analysis Widget
**Type**: Area Chart  
**Purpose**: Analyze Pinterest trending keywords and seasonal performance patterns.

**Features**:
- Trending keywords analysis
- Seasonal performance tracking
- Growth rate calculation
- Trend score assessment

**Data Points**:
- Trending keywords with growth rates
- Seasonal performance data
- Growth rates for key metrics
- Overall trend score

### 7. Cross-Platform Pinterest Comparison Widget
**Type**: Multi-Bar Chart  
**Purpose**: Compare Pinterest performance against other platforms (Meta, Google) with attribution analysis.

**Features**:
- Platform performance comparison
- Attribution score analysis
- Pinterest optimization insights
- Cross-platform ROI comparison

**Data Points**:
- Platform impressions, clicks, CTR
- Attribution scores
- Pinterest share of total performance
- Cross-platform optimization recommendations

## 🔧 Technical Implementation

### Core Components

#### PinterestAnalyticsWidgets Class
Main class that orchestrates all Pinterest analytics widgets.

**Key Methods**:
- `get_campaign_roi_widget()`: Generate campaign ROI comparison
- `get_pin_performance_widget()`: Generate pin performance analysis
- `get_audience_demographics_widget()`: Generate audience demographics
- `get_purchase_funnel_widget()`: Generate purchase funnel visualization
- `get_discovery_phase_widget()`: Generate discovery phase metrics
- `get_trend_analysis_widget()`: Generate trend analysis
- `get_cross_platform_widget()`: Generate cross-platform comparison
- `get_all_widgets()`: Generate all widgets at once

#### PinterestWidgetData Class
Data structure for Pinterest widget data with metadata.

**Attributes**:
- `widget_id`: Unique widget identifier
- `widget_type`: Chart type (bar_chart, scatter_plot, etc.)
- `title`: Widget display title
- `data`: Widget data dictionary
- `metadata`: Additional metadata
- `last_updated`: Timestamp of last update

### Integration Points

#### Pinterest Dashboard Integration
- Uses `PinterestDashboardIntegration` for Pinterest API data
- Fetches campaigns, ad groups, and ads data
- Handles pagination and error cases

#### Cross-Platform Attribution
- Integrates with `IntegratedCrossPlatformAttribution` for multi-platform analysis
- Provides attribution scoring and optimization insights
- Enables cross-platform performance comparison

#### Feed Enhancement Integration
- Uses Pinterest trends and audience insights
- Generates customer personas
- Provides trending keywords analysis

## 📈 Widget Data Structure

### Campaign ROI Widget Data
```json
{
  "campaigns": [
    {
      "campaign_id": "string",
      "campaign_name": "string",
      "roas": 2.5,
      "cpa": 25.0,
      "revenue": 500.0,
      "spend": 200.0,
      "impressions": 5000,
      "clicks": 250,
      "purchases": 20
    }
  ],
  "summary": {
    "total_campaigns": 5,
    "avg_roas": 2.3,
    "total_revenue": 2500.0,
    "total_spend": 1000.0,
    "best_campaign": {...}
  },
  "chart_data": {
    "labels": ["Campaign 1", "Campaign 2"],
    "datasets": [...]
  }
}
```

### Pin Performance Widget Data
```json
{
  "pins": [
    {
      "pin_id": "string",
      "ad_id": "string",
      "campaign_id": "string",
      "impressions": 1000,
      "clicks": 50,
      "saves": 25,
      "ctr": 5.0,
      "save_rate": 2.5,
      "spend": 30.0,
      "revenue": 75.0
    }
  ],
  "summary": {
    "total_pins": 100,
    "top_pins_count": 50,
    "avg_ctr": 3.2,
    "avg_save_rate": 2.1,
    "total_impressions": 50000,
    "total_clicks": 2500,
    "total_saves": 1250
  }
}
```

### Audience Demographics Widget Data
```json
{
  "persona": {
    "name": "Fashion Enthusiast",
    "generated_at": "2024-01-15T10:30:00Z"
  },
  "demographics": {
    "age_groups": ["25-34", "35-44"],
    "genders": ["female", "male"],
    "interests": ["Fashion", "Beauty", "Lifestyle"]
  },
  "behavior": {
    "top_categories": ["Fashion", "Beauty"],
    "engagement_patterns": ["high_engagement", "seasonal_shopper"]
  }
}
```

## 🚀 Usage Examples

### Basic Usage
```python
from pinterest_analytics_widgets import PinterestAnalyticsWidgets
from datetime import datetime, timedelta

# Initialize widgets
widgets = PinterestAnalyticsWidgets()

# Set date range
end_date = datetime.now()
start_date = end_date - timedelta(days=30)

# Get all widgets
all_widgets = widgets.get_all_widgets(start_date, end_date)

# Get specific widget
roi_widget = widgets.get_campaign_roi_widget(start_date, end_date)
```

### Convenience Functions
```python
from pinterest_analytics_widgets import get_pinterest_analytics_widgets, get_specific_pinterest_widget

# Get all widgets
widgets = get_pinterest_analytics_widgets(start_date, end_date)

# Get specific widget
roi_widget = get_specific_pinterest_widget("campaign_roi", start_date, end_date)
```

### Integration with Track AI Dashboard
```python
# Initialize with Track AI API key
widgets = PinterestAnalyticsWidgets(track_ai_api_key="your_api_key")

# Get widgets for dashboard
dashboard_widgets = widgets.get_all_widgets(start_date, end_date)

# Process widgets for dashboard display
for widget in dashboard_widgets:
    if not widget.data.get("empty", False):
        # Display widget in dashboard
        display_widget(widget)
```

## 🧪 Testing

### Test Suite
The `test_pinterest_analytics_widgets.py` file provides comprehensive testing for all widgets:

- **Initialization Tests**: Verify widget system setup
- **Individual Widget Tests**: Test each widget type
- **Integration Tests**: Test with mock data
- **Convenience Function Tests**: Test helper functions
- **Error Handling Tests**: Test error scenarios

### Running Tests
```bash
python test_pinterest_analytics_widgets.py
```

### Test Coverage
- ✅ Widget initialization
- ✅ Campaign ROI widget
- ✅ Pin performance widget
- ✅ Audience demographics widget
- ✅ Purchase funnel widget
- ✅ Discovery phase widget
- ✅ Trend analysis widget
- ✅ Cross-platform widget
- ✅ All widgets integration
- ✅ Convenience functions

## 🔧 Configuration

### Environment Variables
```bash
# Track AI Configuration
TRACK_AI_API_KEY=your_track_ai_api_key
TRACK_AI_PIXEL_ID=your_pixel_id

# Pinterest Configuration
PINTEREST_APP_ID=your_app_id
PINTEREST_APP_SECRET=your_app_secret

# Optional: Bitly for URL shortening
BITLY_ACCESS_TOKEN=your_bitly_token
```

### Widget Configuration
```python
# Customize widget behavior
widgets = PinterestAnalyticsWidgets()

# Configure specific widgets
roi_widget = widgets.get_campaign_roi_widget(
    start_date, 
    end_date, 
    campaign_ids=["camp_1", "camp_2"]  # Filter specific campaigns
)

pin_widget = widgets.get_pin_performance_widget(
    start_date, 
    end_date, 
    top_n=25  # Top 25 performing pins
)
```

## 📊 Dashboard Integration

### Chart.js Integration
The widgets are designed to work with Chart.js v4 for visualization:

```javascript
// Example Chart.js integration
const widgetData = {
  type: 'bar',
  data: {
    labels: widget.chart_data.labels,
    datasets: widget.chart_data.datasets
  },
  options: {
    responsive: true,
    plugins: {
      title: {
        display: true,
        text: widget.title
      }
    }
  }
};
```

### React/TypeScript Integration
```typescript
interface PinterestWidget {
  widget_id: string;
  widget_type: string;
  title: string;
  data: any;
  metadata: any;
  last_updated: string;
}

// Use in React component
const PinterestAnalyticsDashboard: React.FC = () => {
  const [widgets, setWidgets] = useState<PinterestWidget[]>([]);
  
  useEffect(() => {
    // Fetch widgets from API
    fetchPinterestWidgets().then(setWidgets);
  }, []);
  
  return (
    <div className="pinterest-analytics-dashboard">
      {widgets.map(widget => (
        <WidgetRenderer key={widget.widget_id} widget={widget} />
      ))}
    </div>
  );
};
```

## 🔍 Error Handling

### Common Error Scenarios
1. **No Pinterest Data**: Widgets return empty state with error message
2. **API Failures**: Graceful degradation with mock data
3. **Missing Dependencies**: Clear error messages for missing integrations
4. **Invalid Date Ranges**: Validation and fallback to default ranges

### Error Response Format
```json
{
  "widget_id": "campaign_roi",
  "widget_type": "empty",
  "title": "Pinterest Campaign ROI Comparison",
  "data": {
    "error": "No Pinterest data available",
    "empty": true
  },
  "metadata": {
    "error": true
  }
}
```

## 🚀 Performance Optimization

### Caching
- Widget data is cached with timestamps
- Refresh logic prevents unnecessary API calls
- Configurable cache TTL

### Rate Limiting
- Respects Pinterest API rate limits
- Implements exponential backoff
- Batch processing for multiple widgets

### Memory Management
- Efficient data structures
- Lazy loading for large datasets
- Garbage collection for unused widgets

## 📈 Future Enhancements

### Planned Features
1. **Real-time Updates**: WebSocket integration for live data
2. **Predictive Analytics**: ML-based performance predictions
3. **Custom Widgets**: User-defined widget creation
4. **Export Functionality**: PDF/Excel export capabilities
5. **Mobile Optimization**: Responsive design improvements

### Integration Roadmap
1. **Advanced Attribution**: Multi-touch attribution models
2. **AI Insights**: Automated optimization recommendations
3. **Competitive Analysis**: Benchmark against industry standards
4. **Seasonal Trends**: Advanced seasonal pattern recognition

## 📚 API Reference

### PinterestAnalyticsWidgets Methods

#### `__init__(track_ai_api_key: str = None)`
Initialize Pinterest analytics widgets system.

#### `get_campaign_roi_widget(start_date: datetime, end_date: datetime, campaign_ids: List[str] = None) -> PinterestWidgetData`
Generate campaign ROI comparison widget.

#### `get_pin_performance_widget(start_date: datetime, end_date: datetime, top_n: int = 50) -> PinterestWidgetData`
Generate pin performance analysis widget.

#### `get_audience_demographics_widget(start_date: datetime, end_date: datetime) -> PinterestWidgetData`
Generate audience demographics widget.

#### `get_purchase_funnel_widget(start_date: datetime, end_date: datetime) -> PinterestWidgetData`
Generate purchase funnel visualization widget.

#### `get_discovery_phase_widget(start_date: datetime, end_date: datetime) -> PinterestWidgetData`
Generate discovery phase metrics widget.

#### `get_trend_analysis_widget(start_date: datetime, end_date: datetime) -> PinterestWidgetData`
Generate trend analysis widget.

#### `get_cross_platform_widget(start_date: datetime, end_date: datetime) -> PinterestWidgetData`
Generate cross-platform comparison widget.

#### `get_all_widgets(start_date: datetime, end_date: datetime) -> List[PinterestWidgetData]`
Generate all Pinterest analytics widgets.

### Convenience Functions

#### `get_pinterest_analytics_widgets(start_date: datetime, end_date: datetime, track_ai_api_key: str = None) -> List[PinterestWidgetData]`
Get all Pinterest analytics widgets for a date range.

#### `get_specific_pinterest_widget(widget_type: str, start_date: datetime, end_date: datetime, track_ai_api_key: str = None, **kwargs) -> PinterestWidgetData`
Get a specific Pinterest analytics widget.

## 🎯 Best Practices

### Widget Usage
1. **Date Ranges**: Use appropriate date ranges (7-30 days for optimal performance)
2. **Error Handling**: Always check for empty widgets and handle errors gracefully
3. **Caching**: Implement caching for frequently accessed widgets
4. **Responsive Design**: Ensure widgets work on all screen sizes

### Performance
1. **Batch Processing**: Use `get_all_widgets()` for multiple widgets
2. **Lazy Loading**: Load widgets on demand
3. **Data Filtering**: Use campaign_ids and other filters to reduce data volume
4. **Memory Management**: Clean up unused widget data

### Integration
1. **API Keys**: Store API keys securely in environment variables
2. **Rate Limiting**: Implement proper rate limiting for API calls
3. **Monitoring**: Add logging and monitoring for widget performance
4. **Testing**: Use comprehensive test suite for reliability

## 📞 Support

For questions, issues, or feature requests related to Pinterest Analytics Widgets:

1. **Documentation**: Check this documentation first
2. **Tests**: Run the test suite to verify functionality
3. **Logs**: Check application logs for error details
4. **Integration**: Verify all required dependencies are installed

## 🔄 Version History

### v1.0.0 (Current)
- Initial release with 7 core widgets
- Pinterest API integration
- Cross-platform attribution
- Comprehensive testing suite
- Documentation and examples

### Planned v1.1.0
- Real-time widget updates
- Enhanced error handling
- Performance optimizations
- Additional widget types

### Planned v2.0.0
- AI-powered insights
- Custom widget creation
- Advanced attribution models
- Mobile-first design
