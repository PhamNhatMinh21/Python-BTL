import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
import seaborn as sns

df = pd.read_csv('results.csv')

numeric_df = df.select_dtypes(include='number')
numeric_df = numeric_df.dropna(axis=1)
scaler = StandardScaler()
scaled_data = scaler.fit_transform(numeric_df)

inertias = [] 
K = range(1, 11)
for k in K:
    kmeans = KMeans(n_clusters=k, random_state=42)
    kmeans.fit(scaled_data)
    inertias.append(kmeans.inertia_)

plt.figure(figsize=(8, 5)) 
plt.plot(K, inertias, marker='o', linestyle='-', linewidth=1, markersize=5)
plt.title('Elbow Method - Xác định số lượng nhóm (k)', fontsize=10, fontweight='bold')
plt.xlabel('Số lượng nhóm (k)', fontsize=10)
plt.ylabel('Inertia', fontsize=10)
plt.grid(True)

optimal_k = 3
plt.axvline(x=optimal_k, color='red', linestyle='--', label='Elbow tại k=3')
elbow_point = inertias[optimal_k - 1]
plt.annotate('K cần tìm', 
             xy=(optimal_k, elbow_point),
             xytext=(optimal_k + 1, elbow_point + 800),
             arrowprops=dict(facecolor='black', shrink=0.00),
             fontsize=7, fontweight='bold')
plt.legend()
plt.show()

k = 3
kmeans = KMeans(n_clusters=k, random_state=42)
df['Cluster'] = kmeans.fit_predict(scaled_data)

pca = PCA(n_components=2)
pca_result = pca.fit_transform(scaled_data)
df['PCA1'] = pca_result[:, 0]
df['PCA2'] = pca_result[:, 1]

centroids = kmeans.cluster_centers_
centroids_pca = pca.transform(centroids)
plt.figure(figsize=(10, 7))
sns.scatterplot(data=df, x='PCA1', y='PCA2', hue='Cluster', palette='Set2', s=60)
plt.scatter(centroids_pca[:, 0], centroids_pca[:, 1], c='red', marker='x', s=200, linewidths=3, label='Tâm cụm')
plt.title('Phân cụm cầu thủ (PCA + K-means)')
plt.xlabel('Thành phần chính 1 (PCA1)')
plt.ylabel('Thành phần chính 2 (PCA2)')
plt.legend(title='Cụm')
plt.grid(True)
plt.show()