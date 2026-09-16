"""Python analysis for the Consumer Electronics Supply Chain project.

This script reads CSV files, cleans/merges data, summarizes data,
calculates simple metrics, creates charts, and saves the charts.
"""

import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

# Change these two folders when running the script on another computer.
DATA_FOLDER = "/Dataset"
OUTPUT_FOLDER = "/Output"


def save_chart(file_name):
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_FOLDER, file_name), dpi=150)
    plt.close()


def main():
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)

    sns.set_style("whitegrid")

    # Load the ten project tables.
    customer = pd.read_csv(os.path.join(DATA_FOLDER, "dim_customer.csv"))
    date = pd.read_csv(os.path.join(DATA_FOLDER, "dim_date.csv"))
    facility = pd.read_csv(os.path.join(DATA_FOLDER, "dim_facility.csv"))
    product = pd.read_csv(os.path.join(DATA_FOLDER, "dim_product.csv"))
    supplier = pd.read_csv(os.path.join(DATA_FOLDER, "dim_supplier.csv"))
    inventory = pd.read_csv(os.path.join(DATA_FOLDER, "fact_inventory.csv"))
    procurement = pd.read_csv(os.path.join(DATA_FOLDER, "fact_procurement.csv"))
    production = pd.read_csv(os.path.join(DATA_FOLDER, "fact_production.csv"))
    sales = pd.read_csv(os.path.join(DATA_FOLDER, "fact_sales.csv"))
    shipment = pd.read_csv(os.path.join(DATA_FOLDER, "fact_shipment.csv"))

    # Convert date column.
    date["date"] = pd.to_datetime(date["date"])

    # Merge lookup information into fact tables.
    sales = sales.merge(
        date[["date_key", "date"]],
        on="date_key"
    )

    sales = sales.merge(
        product[["product_id", "product_name"]],
        on="product_id"
    )

    sales = sales.merge(
        customer[["customer_id", "customer_name"]],
        on="customer_id"
    )

    production = production.merge(
        product[["product_id", "product_name"]],
        on="product_id"
    )

    production = production.merge(
        facility[["facility_id", "facility_name", "annual_capacity"]],
        on="facility_id"
    )

    procurement = procurement.merge(
        supplier[["supplier_id", "supplier_name"]],
        on="supplier_id"
    )

    inventory = inventory.merge(
        product[["product_id", "product_name", "unit_cost"]],
        on="product_id"
    )

    # ---------------------------------------------------------
    # Q01: Basic data quality checks
    # ---------------------------------------------------------

    total_rows = (
        len(customer)
        + len(date)
        + len(facility)
        + len(product)
        + len(supplier)
        + len(inventory)
        + len(procurement)
        + len(production)
        + len(sales)
        + len(shipment)
    )

    total_missing = (
        customer.isna().sum().sum()
        + date.isna().sum().sum()
        + facility.isna().sum().sum()
        + product.isna().sum().sum()
        + supplier.isna().sum().sum()
        + inventory.isna().sum().sum()
        + procurement.isna().sum().sum()
        + production.isna().sum().sum()
        + sales.isna().sum().sum()
        + shipment.isna().sum().sum()
    )

    print("\nQ01 - Data Quality")
    print(f"Total rows: {total_rows:,}")
    print(f"Missing values: {total_missing:,}")

    # ---------------------------------------------------------
    # Q02: Monthly revenue
    # ---------------------------------------------------------

    sales["month"] = sales["date"].dt.to_period("M").astype(str)

    monthly_revenue = (
        sales.groupby("month", as_index=False)["net_revenue"]
        .sum()
    )

    best_month = monthly_revenue.loc[
        monthly_revenue["net_revenue"].idxmax()
    ]

    print("\nQ02 - Monthly Revenue")
    print(
        f"{best_month['month']} was highest at "
        f"${best_month['net_revenue']:,.0f}"
    )

    plt.figure(figsize=(10, 4))

    sns.lineplot(
        data=monthly_revenue,
        x="month",
        y="net_revenue",
        marker="o"
    )

    plt.xticks(rotation=45)
    plt.title("Q02 - Monthly Net Revenue")
    plt.xlabel("Month")
    plt.ylabel("Net Revenue ($)")

    save_chart("q02_monthly_revenue.png")

    # ---------------------------------------------------------
    # Q03-Q04: Product revenue and margin
    # ---------------------------------------------------------

    product_sales = (
        sales.groupby("product_name", as_index=False)
        .agg(
            revenue=("net_revenue", "sum"),
            profit=("profit", "sum")
        )
    )

    product_sales["margin"] = (
        product_sales["profit"]
        / product_sales["revenue"]
        * 100
    )

    best_product = product_sales.loc[
        product_sales["revenue"].idxmax()
    ]

    best_margin = product_sales.loc[
        product_sales["margin"].idxmax()
    ]

    print("\nQ03 - Product Revenue")
    print(
        f"{best_product['product_name']} led with "
        f"${best_product['revenue']:,.0f}"
    )

    print("\nQ04 - Product Margin")
    print(
        f"{best_margin['product_name']} led with "
        f"{best_margin['margin']:.2f}%"
    )

    chart_data = (
        product_sales
        .nlargest(8, "revenue")
        .sort_values("revenue")
    )

    plt.figure(figsize=(8, 5))

    sns.barplot(
        data=chart_data,
        y="product_name",
        x="revenue"
    )

    plt.title("Q03 - Products with Highest Net Revenue")
    plt.xlabel("Net Revenue ($)")
    plt.ylabel("Product")

    save_chart("q03_product_revenue.png")

    # ---------------------------------------------------------
    # Q05: Discount and margin
    # ---------------------------------------------------------

    correlation = sales["discount_pct"].corr(
        sales["profit_margin_pct"]
    )

    print("\nQ05 - Discount and Margin")
    print(
        f"Correlation between discount and profit margin: "
        f"{correlation:.2f}"
    )

    plt.figure(figsize=(7, 5))

    sns.scatterplot(
        data=sales,
        x="discount_pct",
        y="profit_margin_pct",
        alpha=0.35
    )

    plt.title("Q05 - Discount Percentage and Profit Margin")
    plt.xlabel("Discount (%)")
    plt.ylabel("Profit Margin (%)")

    save_chart("q05_discount_margin.png")

    # ---------------------------------------------------------
    # Q06: Customer concentration
    # ---------------------------------------------------------

    customer_sales = (
        sales.groupby("customer_name", as_index=False)["net_revenue"]
        .sum()
    )

    customer_sales["share"] = (
        customer_sales["net_revenue"]
        / customer_sales["net_revenue"].sum()
        * 100
    )

    top_two_share = (
        customer_sales
        .nlargest(2, "share")["share"]
        .sum()
    )

    print("\nQ06 - Customer Concentration")
    print(
        f"Top two customers generated "
        f"{top_two_share:.2f}% of net revenue"
    )

    plt.figure(figsize=(8, 4))

    sns.barplot(
        data=customer_sales.sort_values("share"),
        y="customer_name",
        x="share"
    )

    plt.title("Q06 - Customer Share of Net Revenue")
    plt.xlabel("Share (%)")
    plt.ylabel("Customer")

    save_chart("q06_customer_share.png")

    # ---------------------------------------------------------
    # Q07-Q08: Supplier analysis
    # ---------------------------------------------------------

    supplier_summary = (
        procurement.groupby("supplier_name", as_index=False)
        .agg(
            average_lead_time=("lead_time_days", "mean"),
            average_quality=("quality_score", "mean")
        )
    )

    fastest = supplier_summary.loc[
        supplier_summary["average_lead_time"].idxmin()
    ]

    lead_quality_correlation = procurement[
        "lead_time_days"
    ].corr(
        procurement["quality_score"]
    )

    print("\nQ07 - Supplier Lead Time")
    print(
        f"{fastest['supplier_name']} was fastest at "
        f"{fastest['average_lead_time']:.2f} days"
    )

    print("\nQ08 - Supplier Quality and Lead Time")
    print(
        f"Correlation: {lead_quality_correlation:.2f}"
    )

    plt.figure(figsize=(8, 5))

    sns.scatterplot(
        data=supplier_summary,
        x="average_lead_time",
        y="average_quality",
        s=120
    )

    for _, row in supplier_summary.iterrows():
        plt.text(
            row["average_lead_time"],
            row["average_quality"],
            row["supplier_name"],
            fontsize=8
        )

    plt.title("Q07-Q08 - Supplier Lead Time and Quality")
    plt.xlabel("Average Lead Time (Days)")
    plt.ylabel("Average Quality Score")

    save_chart("q07_q08_supplier_summary.png")

    # ---------------------------------------------------------
    # Q09-Q10: Production quality and capacity
    # ---------------------------------------------------------

    product_production = (
        production.groupby("product_name", as_index=False)
        .agg(
            units=("quantity_produced", "sum"),
            defects=("defective_units", "sum")
        )
    )

    product_production["defect_rate"] = (
        product_production["defects"]
        / product_production["units"]
        * 100
    )

    worst_defect = product_production.loc[
        product_production["defect_rate"].idxmax()
    ]

    facility_production = (
        production
        .groupby(
            [
                "facility_id",
                "facility_name",
                "annual_capacity"
            ],
            as_index=False
        )["quantity_produced"]
        .sum()
    )

    facility_production["capacity_used"] = (
        facility_production["quantity_produced"]
        / facility_production["annual_capacity"]
        * 100
    )

    highest_capacity = facility_production.loc[
        facility_production["capacity_used"].idxmax()
    ]

    print("\nQ09 - Production Defects")
    print(
        f"{worst_defect['product_name']} had the highest "
        f"defect rate at {worst_defect['defect_rate']:.3f}%"
    )

    print("\nQ10 - Facility Capacity")
    print(
        f"{highest_capacity['facility_name']} used "
        f"{highest_capacity['capacity_used']:.2f}% "
        f"of stated capacity"
    )

    fig, axes = plt.subplots(
        1,
        2,
        figsize=(12, 5)
    )

    sns.barplot(
        data=product_production.sort_values("defect_rate"),
        y="product_name",
        x="defect_rate",
        ax=axes[0]
    )

    axes[0].set_title("Q09 - Production Defect Rate")
    axes[0].set_xlabel("Defect Rate (%)")
    axes[0].set_ylabel("Product")

    sns.barplot(
        data=facility_production.sort_values("capacity_used"),
        y="facility_name",
        x="capacity_used",
        ax=axes[1]
    )

    axes[1].axvline(
        100,
        color="red",
        linestyle="--"
    )

    axes[1].set_title("Q10 - Production vs Stated Capacity")
    axes[1].set_xlabel("Capacity Used (%)")
    axes[1].set_ylabel("Facility")

    save_chart("q09_q10_production.png")

    # ---------------------------------------------------------
    # Q11-Q12: Latest inventory risk
    # ---------------------------------------------------------

    latest_date_key = inventory["date_key"].max()

    latest_inventory = inventory[
        inventory["date_key"] == latest_date_key
    ].copy()

    latest_inventory["units_vs_reorder"] = (
        latest_inventory["stock_level"]
        - latest_inventory["reorder_point"]
    )

    below_reorder = latest_inventory[
        latest_inventory["units_vs_reorder"] < 0
    ]

    latest_inventory["excess_value"] = np.where(
        latest_inventory["units_vs_reorder"] > 0,
        latest_inventory["units_vs_reorder"]
        * latest_inventory["unit_cost"],
        0
    )

    largest_excess = (
        latest_inventory
        .groupby("product_name", as_index=False)["excess_value"]
        .sum()
    )

    largest_excess = largest_excess.loc[
        largest_excess["excess_value"].idxmax()
    ]

    print("\nQ11 - Inventory Below Reorder Point")
    print(
        f"{len(below_reorder)} of "
        f"{len(latest_inventory)} snapshots were "
        f"below reorder point"
    )

    print("\nQ12 - Excess Inventory Value")
    print(
        f"{largest_excess['product_name']} had "
        f"${largest_excess['excess_value']:,.0f} "
        f"excess inventory value"
    )

    inventory_chart = (
        latest_inventory
        .groupby("product_name", as_index=False)["excess_value"]
        .sum()
        .nlargest(8, "excess_value")
    )

    plt.figure(figsize=(8, 5))

    sns.barplot(
        data=inventory_chart,
        y="product_name",
        x="excess_value"
    )

    plt.title("Q12 - Products with Highest Excess Inventory Value")
    plt.xlabel("Excess Value ($)")
    plt.ylabel("Product")

    save_chart("q11_q12_inventory.png")

    # ---------------------------------------------------------
    # Q13-Q15: Shipment analysis
    # ---------------------------------------------------------

    shipment["delayed"] = (
        shipment["status"] == "Delayed"
    )

    carrier_summary = (
        shipment.groupby("carrier", as_index=False)
        .agg(
            shipments=("shipment_id", "count"),
            delayed=("delayed", "sum")
        )
    )

    carrier_summary["delay_rate"] = (
        carrier_summary["delayed"]
        / carrier_summary["shipments"]
        * 100
    )

    highest_delay = carrier_summary.loc[
        carrier_summary["delay_rate"].idxmax()
    ]

    reasons = (
        shipment[shipment["delayed"]]["delay_reason"]
        .value_counts()
    )

    delayed_cost = shipment.loc[
        shipment["delayed"],
        "shipping_cost"
    ].mean()

    on_time_cost = shipment.loc[
        ~shipment["delayed"],
        "shipping_cost"
    ].mean()

    print("\nQ13 - Carrier Delays")
    print(
        f"{highest_delay['carrier']} had the highest "
        f"delay rate at {highest_delay['delay_rate']:.2f}%"
    )

    print("\nQ14 - Delay Reasons")

    if len(reasons) > 0:
        print(
            f"{reasons.index[0]} was the most common reason "
            f"with {reasons.iloc[0]} cases"
        )
    else:
        print("No delayed shipments were recorded.")

    print("\nQ15 - Average Shipping Cost")
    print(
        f"Delayed shipments: ${delayed_cost:,.0f}"
    )
    print(
        f"Non-delayed shipments: ${on_time_cost:,.0f}"
    )

    fig, axes = plt.subplots(
        1,
        2,
        figsize=(12, 5)
    )

    sns.barplot(
        data=carrier_summary.sort_values("delay_rate"),
        y="carrier",
        x="delay_rate",
        ax=axes[0]
    )

    axes[0].set_title("Q13 - Carrier Delay Rate")
    axes[0].set_xlabel("Delayed Shipments (%)")
    axes[0].set_ylabel("Carrier")

    if len(reasons) > 0:
        sns.barplot(
            x=reasons.values,
            y=reasons.index,
            ax=axes[1]
        )

    axes[1].set_title("Q14 - Shipment Delay Reasons")
    axes[1].set_xlabel("Delayed Shipments")
    axes[1].set_ylabel("Delay Reason")

    save_chart("q13_q14_shipments.png")

    # ---------------------------------------------------------
    # Final message
    # ---------------------------------------------------------

    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE")
    print("=" * 60)
    print(f"Charts saved to: {OUTPUT_FOLDER}")
    print("\nFiles created:")

    chart_files = [
        "q02_monthly_revenue.png",
        "q03_product_revenue.png",
        "q05_discount_margin.png",
        "q06_customer_share.png",
        "q07_q08_supplier_summary.png",
        "q09_q10_production.png",
        "q11_q12_inventory.png",
        "q13_q14_shipments.png"
    ]

    for file_name in chart_files:
        print(f"  - {file_name}")


if __name__ == "__main__":
    main()