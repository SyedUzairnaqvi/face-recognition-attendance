# Power BI Analytics Setup

The project already exposes a production-ready analytics endpoint:

`https://secure-vision-attendance.onrender.com/analytics/dashboard`

It is backed by the deployed MySQL database and returns:

- KPI totals: registered people, attendance records, recognition events, recognition rate
- Daily attendance
- Recognition by source/result
- Person attendance
- Video analytics

## Fastest Power BI connection

Use the **Web** connector rather than exposing the MySQL server directly to Power BI. This keeps the BI layer dependent on the existing HTTPS API and avoids putting database credentials into the PBIX file.

### 1. Power BI Desktop

Open the existing `Secure_Vision_Attendance_Analytics.pbix` file.

Choose:

`Home -> Transform data -> Transform data`

Then create these queries in Power Query.

### 2. Base query

Create a blank query named `AnalyticsDashboard` and use:

```powerquery
let
    Source = Json.Document(
        Web.Contents("https://secure-vision-attendance.onrender.com/analytics/dashboard")
    )
in
    Source
```

### 3. KPI table

```powerquery
let
    Source = AnalyticsDashboard,
    Output = #table(
        {"Metric", "Value"},
        {
            {"Registered People", Source[registered_people]},
            {"Attendance Records", Source[attendance_records]},
            {"Recognition Events", Source[recognition_events]},
            {"Recognition Rate %", Source[recognition_rate]}
        }
    )
in
    Output
```

Name it `KPI`.

### 4. Daily Attendance

```powerquery
let
    Source = AnalyticsDashboard[daily_attendance],
    Table = Table.FromRecords(Source),
    Types = Table.TransformColumnTypes(
        Table,
        {
            {"date", type date},
            {"attendance_records", Int64.Type},
            {"people_present", Int64.Type}
        }
    )
in
    Types
```

Name it `DailyAttendance`.

### 5. Recognition by Source

```powerquery
let
    Source = AnalyticsDashboard[recognition_by_source],
    Table = Table.FromRecords(Source),
    Types = Table.TransformColumnTypes(
        Table,
        {
            {"source", type text},
            {"total_events", Int64.Type},
            {"matched_events", Int64.Type},
            {"unknown_events", Int64.Type}
        }
    )
in
    Types
```

Name it `RecognitionBySource`.

### 6. Person Attendance

```powerquery
let
    Source = AnalyticsDashboard[person_attendance],
    Table = Table.FromRecords(Source),
    Types = Table.TransformColumnTypes(
        Table,
        {
            {"name", type text},
            {"attendance_count", Int64.Type},
            {"last_attendance", type date}
        }
    )
in
    Types
```

Name it `PersonAttendance`.

### 7. Video Analytics

```powerquery
let
    Source = AnalyticsDashboard[video_analytics],
    Table = Table.FromRecords({Source}),
    Types = Table.TransformColumnTypes(
        Table,
        {
            {"total_videos", Int64.Type},
            {"total_faces_detected", Int64.Type},
            {"total_recognized_faces", Int64.Type},
            {"total_unknown_faces", Int64.Type}
        }
    )
in
    Types
```

Name it `VideoAnalytics`.

## Recommended report visuals

Create one Power BI report page called **Secure Vision Attendance Analytics**.

### KPI cards

- Registered People
- Attendance Records
- Recognition Events
- Recognition Rate %

### Charts

1. **Daily Attendance** — line chart
   - X-axis: `DailyAttendance[date]`
   - Values: `people_present`, `attendance_records`

2. **Recognition by Source** — clustered column chart
   - X-axis: `RecognitionBySource[source]`
   - Values: `matched_events`, `unknown_events`

3. **Attendance by Person** — bar chart
   - Axis: `PersonAttendance[name]`
   - Value: `PersonAttendance[attendance_count]`

4. **Video Processing** — cards/table
   - Total videos
   - Faces detected
   - Recognized faces
   - Unknown faces

## Refresh

Use **Refresh** in Power BI Desktop to pull the latest production data from Render.

For Power BI Service scheduled refresh, publish the report and configure the dataset refresh settings. Because the source is HTTPS, no local MySQL gateway is required for this API-based approach.

## Security

Do not place MySQL usernames/passwords in the PBIX file or repository. The Power BI setup above consumes the existing HTTPS analytics API and keeps database credentials server-side.

## Current validation

The production endpoint has already been verified to return live MySQL data with:

- `database_connected: true`
- registered people
- attendance records
- recognition events
- recognition rate
- daily attendance
- recognition source breakdown
- person attendance
- video analytics

The existing `docs/analytics.sql` remains available for direct MySQL reporting and SQL-based BI work.