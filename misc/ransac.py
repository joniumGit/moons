"""
Miscellaneous RANSAC Test file
"""

if __name__ == '__main__':
    from typing import Tuple

    import matplotlib.pyplot as plt
    import numpy as np
    from sklearn.linear_model import RANSACRegressor, LinearRegression, HuberRegressor
    from sklearn.metrics import mean_squared_error
    from sklearn.pipeline import make_pipeline, Pipeline
    from sklearn.preprocessing import PolynomialFeatures

    plt.switch_backend("tkagg")


    def equation(x: np.ndarray, params: np.ndarray) -> np.ndarray:
        data = params[0] * x ** 2 + params[1] * x + params[2]
        return (data - np.min(data)) * 1 / (np.max(data) - np.min(data))


    def noised(x: np.ndarray, y: np.ndarray, noise: float = 0.05) -> Tuple[np.ndarray, np.ndarray]:
        outliers = int(np.sqrt(len(x)))
        combined = np.column_stack((x, y))
        n = random.normal(scale=noise, size=combined.shape)
        combined = combined + n
        combined[len(y) // 2 - outliers // 2:len(y) // 2 + outliers // 2, 1] = np.max(y)
        return combined[:, 0], combined[:, 1]


    for state in [0, 2, 5]:
        # 0, 2, 5
        random = np.random.RandomState(state)
        test_params = random.randn(3, 1)

        for num in [100, 1024, 10000]:
            test_x = np.linspace(0, 1, num=num)
            test_y = equation(test_x, test_params)
            test_noise = np.std(test_y) / 4
            noised_x, noised_y = noised(test_x, test_y, noise=test_noise)

            plt.scatter(test_x, test_y, c="r", s=2)
            plt.scatter(noised_x, noised_y, c="b", s=2, alpha=0.35)

            for i in [3, np.sqrt(len(test_x)) // 2, int(np.sqrt(len(test_x))), len(test_x) // 2, len(test_x)]:
                pipe: Pipeline = make_pipeline(
                    PolynomialFeatures(
                        2,
                        include_bias=False
                    ),
                    RANSACRegressor(
                        random_state=10,
                        min_samples=i,
                        base_estimator=LinearRegression()
                    )
                )
                pipe.fit(noised_x[..., None], noised_y)
                pred_y = pipe.predict(test_x[..., None])
                mse = mean_squared_error(test_y, pred_y)
                plt.plot(
                    test_x,
                    pred_y,
                    linestyle="--",
                    label=f"{i}, mse: {mse:.5e}, score: {pipe.score(test_x[..., None], test_y):.3f}"
                )

            pipe: Pipeline = make_pipeline(
                PolynomialFeatures(
                    2,
                    include_bias=False
                ),
                LinearRegression()
            )
            pipe.fit(noised_x[..., None], noised_y)
            pred_y = pipe.predict(test_x[..., None])
            mse = mean_squared_error(test_y, pred_y)
            plt.plot(
                test_x,
                pred_y,
                linestyle="--",
                label=f"LinReg, mse: {mse:.5e}, score: {pipe.score(test_x[..., None], test_y):.3f}"
            )

            pipe: Pipeline = make_pipeline(
                PolynomialFeatures(
                    2,
                    include_bias=False
                ),
                HuberRegressor()
            )
            pipe.fit(noised_x[..., None], noised_y)
            pred_y = pipe.predict(test_x[..., None])
            mse = mean_squared_error(test_y, pred_y)
            plt.plot(
                test_x,
                pred_y,
                linestyle="--",
                label=f"Huber, mse: {mse:.5e}, score: {pipe.score(test_x[..., None], test_y):.3f}"
            )

            plt.title(f"random=RandomState({state}); params=random.randn(3, 1); n={num}")
            plt.legend()
            plt.show()
