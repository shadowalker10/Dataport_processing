import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os

# pandas
# df[col][index], df.loc[index, cloumns] ,df.to_numpy()
# numpy
# matrix [row, colums] pd.Datafame(np., columns()...)
# np.arrary() ----- model
# dataframe ----- numpy ---- model ---- numpy ---- dataframe ---- plot
if __name__ == '__main__':
    months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October',
              'November', 'December']
    city = ['Austin', 'Boulder']
    num_city = 0

    for num_mon in range(0, 1):
        # ------------------------------------
        # read the data
        # ------------------------------------
        df_pro = pd.read_csv(
            './processed_data_connected/{}_in_{}_connected.csv'.format(city[num_city], months[num_mon]))
        df_pro = df_pro.set_index('local_15min')
        df_pro = df_pro.drop(['avg'], axis=1)

        # ------------------------------------
        # deal with meta data
        # ------------------------------------
        meta_data = pd.read_csv('./meta_data/metadata.csv')
        meta_data = meta_data[['dataid', 'total_square_footage']]
        col_df = df_pro.columns
        col_df = col_df.to_numpy()
        col_df = col_df.astype('int64')
        meta_data = meta_data.set_index('dataid')
        meta_data_extracted = pd.DataFrame(meta_data, index=col_df)
        # ------------------------------------
        # save the document data in dictionary with key as columns number
        # ------------------------------------
        # dict ---- dataframe
        # dataframe
        # dc: the users' information
        dc = dict()
        # dc_qu: the quantile information
        dc_qu = dict()
        # dc_len: the inter-quantile range of the individual user
        dc_len = dict()
        # dc_len_median: the inter-quantile range divided by the median value
        dc_len_median = dict()

        fit_norm = dict()
        fit_norm_mean = pd.DataFrame()
        fit_norm_std = pd.DataFrame()

        for col in df_pro.columns:
            df_user = df_pro[col].to_numpy().reshape((-1, 48, 2))
            df_user = np.swapaxes(df_user, 1, 2).reshape((-1, 48))
            df_user_pd = pd.DataFrame(df_user, columns=np.arange(48))

            # calculate the quantile number
            df_user_pd_qu = df_user_pd.quantile([0.25, 0.5, 0.75])
            df_user_pd_qu = df_user_pd_qu.T
            df_user_pd_qu['length'] = df_user_pd_qu[0.75] - df_user_pd_qu[0.25]
            # users' load information
            dc[col] = df_user_pd
            dc_qu[col] = df_user_pd_qu
            dc_len[col] = df_user_pd_qu['length']
            dc_len_median[col] = df_user_pd_qu['length'].divide(df_user_pd_qu[0.5])

            # calculate mean and variance
            df_user_des = df_user_pd.describe().T
            df_user_norm = df_user_des[['mean', 'std']]
            fit_norm[col] = df_user_norm
            fit_norm_mean[col] = df_user_norm['mean']
            fit_norm_std[col] = df_user_norm['std']

        df_sum_area = df_pro.sum(axis=1)
        df_sum_area = df_sum_area.to_numpy().reshape((-1, 48, 2))
        df_sum_area = np.swapaxes(df_sum_area, 1, 2).reshape((-1, 48))
        df_sum_area_pd = pd.DataFrame(df_sum_area, columns=np.arange(48))

        # calculate the quantile number
        df_sum_area_qu = df_sum_area_pd.quantile([0.25, 0.5, 0.75])
        df_sum_area_qu = df_sum_area_qu.T
        df_sum_area_qu['length'] = df_sum_area_qu[0.25] - df_sum_area_qu[0.75]

        # calculate mean and variance
        df_sum_norm = df_sum_area_pd.describe().T[['mean', 'std']]
        fit_norm_mean['sum'] = df_sum_norm['mean']
        fit_norm_std['sum'] = df_sum_norm['std']

        # calculate covariance over different users
        # choose according to
        # the u variance and covariance matrix
        # ---------------------------------------------------------
        # for critic_variance in [300, 600, 900, 1200, 1500, 1800, 2100, 3000, 3500, 3800]:
        #     choose_dic = dict()
        #     for num_time in np.arange(48):
        #         df_cov = pd.DataFrame(columns=df_pro.columns)
        #         for col in df_pro.columns:
        #             df_cov[col] = dc[col][num_time]
        #         cov_val = df_cov.cov()
        #         cov_val_sum = cov_val.sum().sum()
        #         choose_col = []
        #         # choose only according to variance
        #         # choose according to the relevance
        #         # why choosing this value?????
        #         aggregated_variance = 0
        #         aggregated_mean = 0
        #         aggregated_col = []
        #         mean_time_num = fit_norm_mean.loc[num_time, :].drop('sum')
        #         while aggregated_variance < critic_variance and mean_time_num.empty is False:
        #             # new_col = mean_time_num.idxmax()
        #             # d_mean = mean_time_num[new_col]
        #             # d_var = 2 * cov_val.loc[choose_col, new_col].sum() + cov_val.loc[new_col, new_col]
        #             k_dic = dict()
        #             for col in mean_time_num.index:
        #                 d_mean = mean_time_num[col]
        #                 d_var = 2 * cov_val.loc[choose_col, col].sum() + cov_val.loc[col, col]
        #                 k_dic[col] = d_mean/d_var
        #             new_col = pd.Series(k_dic).idxmax()
        #             d_mean = mean_time_num[new_col]
        #             d_var = 2 * cov_val.loc[choose_col, new_col].sum() + cov_val.loc[new_col, new_col]
        #             aggregated_mean += d_mean
        #             aggregated_variance += d_var
        #             choose_col.append(new_col)
        #             mean_time_num = mean_time_num.drop(new_col)
        #         choose_dic[num_time] = choose_col
        # plot the mean vs variance curve
        choose_dic = dict()
        for num_time in np.arange(48):
            df_cov = pd.DataFrame(columns=df_pro.columns)
            for col in df_pro.columns:
                df_cov[col] = dc[col][num_time]
            cov_val = df_cov.cov()
            cov_val_sum = cov_val.sum().sum()
            choose_col = []
            choose_mean = []
            choose_variance = []
            aggregated_variance, aggregated_mean = 0, 0
            mean_time_num = fit_norm_mean.loc[num_time, :].drop('sum')
            while aggregated_variance <= cov_val_sum and mean_time_num.empty is False:
                k_dic = dict()
                for col in mean_time_num.index:
                    d_mean = mean_time_num[col]
                    d_var = 2 * cov_val.loc[choose_col, col].sum() + cov_val.loc[col, col]
                    k_dic[col] = d_mean/d_var
                new_col = pd.Series(k_dic).idxmax()
                d_mean = mean_time_num[new_col]
                d_var = 2 * cov_val.loc[choose_col, new_col] + cov_val.loc[new_col, new_col]
                aggregated_mean += d_mean
                aggregated_variance += aggregated_variance
                choose_col.append(new_col)
                choose_mean.append(aggregated_mean)
                choose_variance.append(aggregated_variance)
                mean_time_num = mean_time_num.drop(new_col)
        # -----------------------------------------------------------------------------------
        # plot the aggregated performance
        # -----------------------------------------------------------------------------------
        # for critic_variance in [300, 600, 900, 1200, 1500, 1800, 2100, 3000, 3500, 3800]:
        #     # choose the aggregator
        #     selected_power = dict()
        #     for num_time in np.arange(48):
        #         selected_power[num_time] = pd.Series(np.zeros(df_sum_area.shape[0]))
        #         for col in choose_dic[num_time]:
        #             selected_power[num_time] += dc[col][num_time]
        #     selected_power_pd = pd.DataFrame(selected_power)
        #     try:
        #         os.makedirs('./aggregated_image/{}_{}_aggregated/sns_plot'.format(months[num_mon], city[num_city]))
        #     except OSError:
        #         pass
        #     # plot the confidence value
        #     selected_power_flatten = pd.DataFrame(selected_power_pd.to_numpy().flatten(), columns=['power'])
        #     selected_power_flatten['timepoint'] = list(np.arange(selected_power_pd.shape[1])) * selected_power_pd.shape[0]
        #     fig, ax = plt.subplots()
        #     ax = sns.lineplot(x='timepoint', y='power', data=selected_power_flatten)
        #     plt.title('the_aggregated_with_variance_{2}_in_{0}'.format(months[num_mon], city[num_city], critic_variance))
        #     plt.xlabel('time points')
        #     plt.ylabel('Power/kW')
        #     plt.grid()
        #     plt.xlim((0, 48))
        #     plt.ylim((0, 500))
        #     plt.savefig('./aggregated_image/{}_{}_aggregated/sns_plot/the_aggregated_with_critic_as_{}.png'.
        #                 format(months[num_mon], city[num_city], critic_variance))
        #     plt.close()
        #    # day plot
        #     try:
        #         os.makedirs('./aggregated_image/{0}_{1}_aggregated/day_plot'.format(months[num_mon], city[num_city]))
        #     except OSError:
        #         pass
        #     # plot the aggregated performance:
        #     selected_power_np = selected_power_pd.to_numpy()
        #     fig, ax = plt.subplots()
        #     for day in range(selected_power_np.shape[0]):
        #         ax.plot(selected_power_np[day])
        #     plt.xlabel('time points')
        #     plt.ylabel('Power/kW')
        #     ax.set_ylim((0, 800))
        #     plt.grid()
        #     plt.title('Aggregated_whole_month_with_variance_{2}_in_{0}'
        #               .format(months[num_mon], city[num_city], critic_variance))
        #     plt.savefig('./aggregated_image/{0}_{1}_aggregated/day_plot/the_whole_month_with_critic_as_{2}.png'
        #                 .format(months[num_mon], city[num_city], critic_variance))
        #     plt.close()
        # -------------------------------------------------------------------
        # save the processed data
        # -------------------------------------------------------------------
        # try:
        #     os.makedirs('./data_analysis_norm/{1}_mean'.format(months[num_mon], city[num_city]))
        # except OSError:
        #     pass
        # try:
        #     os.makedirs('./data_analysis_norm/{1}_std'.format(months[num_mon], city[num_city]))
        # except OSError:
        #     pass
        # fit_norm_mean.to_csv('./data_analysis_norm/{1}_mean/{1}_mean_{0}.csv'.format(months[num_mon], city[num_city]))
        # fit_norm_std.to_csv('./data_analysis_norm/{1}_std/{1}_std_{0}.csv'.format(months[num_mon], city[num_city]))

        # ------------------------------------------------------------------
        # set the criterion to choose the users and show the performance
        # need to consider the trade off between the uncertainty and the load power
        # the (kW)
        # the length choose is whether the good parameters???
        # ------------------------------------------------------------------
        # critic_ls = [100, 50, 10, 5, 2.5, 1, 0.5]
        # for critic in critic_ls:
        #     # from the perspective of time scale
        #     selected_power = dict()
        #     ls = list()
        #     selected_flag = pd.DataFrame(np.zeros([48, df_pro.shape[1]]), index=np.arange(48), columns=df_pro.columns)
        #     for t in np.arange(48):
        #         selected_power[t] = pd.Series(np.zeros(df_sum_area.shape[0]))
        #         for col in df_pro.columns:
        #             if dc_len_median[col][t] < critic:
        #                 selected_power[t] += dc[col][t]
        #                 selected_flag.loc[t, col] = True
        #             else:
        #                 selected_flag.loc[t, col] = False
        #     selected_power_pd = pd.DataFrame(selected_power)
        #     selected_power_flatten = pd.DataFrame(selected_power_pd.to_numpy().flatten(), columns=['power'])
        #
        #     try:
        #         os.makedirs('./aggregated_image_len_median/{}_{}_aggregated/box_plot'
        #                     .format(months[num_mon], city[num_city]))
        #     except OSError:
        #         pass
        #     # box plot the aggregated performance
        #     fig, ax = plt.subplots(1, 1)
        #     selected_power_pd.boxplot(column=list(np.arange(48)))
        #     y_top = int(selected_power_pd.max().max()/100)*100 + 100
        #     plt.ylim((0, 800))
        #     plt.xlabel('time points')
        #     plt.ylabel('Power/kW')
        #     plt.title('the aggregated performance in boxplot with critic as {}'.format(critic))
        #     plt.savefig('./aggregated_image_len_median/{}_{}_aggregated/box_plot/the_aggregated_with_critic_as_{}.png'
        #                 .format(months[num_mon], city[num_city], critic))
        #     plt.close()
        #
        #     try:
        #         os.makedirs('./aggregated_image_len_median/{}_{}_aggregated/month_plot'
        #                     .format(months[num_mon], city[num_city]))
        #     except OSError:
        #         pass
        #     # plot the month aggregated performance
        #     fig, ax = plt.subplots()
        #     plt.plot(selected_power_flatten['power'])
        #     ax.set_ylim((0, 800))
        #     plt.grid()
        #     plt.title('Aggregated_whole_month_with_critic_{2}_in_{0}'
        #               .format(months[num_mon], city[num_city], critic))
        #     plt.savefig('./aggregated_image_len_median/{}_{}_aggregated/month_plot/the_whole_month_with_critic_as_{2}'
        #                 .format(months[num_mon], city[num_city], critic))
        #     plt.close()

            # ------------------------------------------------------------------
            # set the criterion to choose the users and show the performance
            # need to consider the trade off between the uncertainty and the load power
            # the (kW)
            # the length choose is whether the good parameters???
            # box plot
            # ------------------------------------------------------------------
            # critic_ls = [100, 50, 10, 5, 2.5, 1, 0.5]
            # for critic in critic_ls:
            #     # from the perspective of time scale
            #     selected_power = dict()
            #     ls = list()
            #     selected_flag = pd.DataFrame(np.zeros([48, df_pro.shape[1]]), index=np.arange(48),
            #                                  columns=df_pro.columns)
            #     for t in np.arange(48):
            #         selected_power[t] = pd.Series(np.zeros(df_sum_area.shape[0]))
            #         for col in df_pro.columns:
            #             if dc_len_median[col][t] < critic:
            #                 selected_power[t] += dc[col][t]
            #                 selected_flag.loc[t, col] = True
            #             else:
            #                 selected_flag.loc[t, col] = False
            #     selected_power_pd = pd.DataFrame(selected_power)
            #     selected_power_flatten = pd.DataFrame(selected_power_pd.to_numpy().flatten(), columns=['power'])
            #
            #     try:
            #         os.makedirs('./aggregated_box_plot/{0}_{1}_aggregated/box_plot'
            #                     .format(months[num_mon], city[num_city]))
            #     except OSError:
            #         pass
            #     # box plot the aggregated performance
            #     fig, ax = plt.subplots(1, 1)
            #     selected_power_pd.boxplot(column=list(np.arange(48)))
            #     plt.ylim((0, 800))
            #     plt.xlabel('time points')
            #     plt.ylabel('Power/kW')
            #     plt.title('the aggregated performance in boxplot with critic as {}'.format(critic))
            #     plt.savefig(
            #         './aggregated_box_plot/{0}_{1}_aggregated/box_plot/the_aggregated_with_critic_as_{2}.png'
            #         .format(months[num_mon], city[num_city], critic))
            #     plt.close()
            #
            #     try:
            #         os.makedirs('./aggregated_box_plot/{0}_{1}_aggregated/day_plot'
            #                     .format(months[num_mon], city[num_city]))
            #     except OSError:
            #         pass
            #     # plot the month aggregated performance
            #     selected_power_np = selected_power_pd.to_numpy()
            #     fig, ax = plt.subplots()
            #     for day in range(selected_power_np.shape[0]):
            #         ax.plot(selected_power_np[day])
            #     ax.set_ylim((0, 800))
            #     plt.xlabel('time points')
            #     plt.ylabel('Power/kW')
            #     plt.grid()
            #     plt.title('Aggregated_whole_month_with_critic_{2}_in_{0}'
            #               .format(months[num_mon], city[num_city], critic))
            #     plt.savefig('./aggregated_box_plot/{0}_{1}_aggregated/day_plot/the_whole_month_with_critic_as_{2}.png'
            #                 .format(months[num_mon], city[num_city], critic))
            #     plt.close()
            #
            # # ------------------------------------------------------------------
            # # stochastic choosing
            # # ------------------------------------------------------------------
            # for the_num_of_choose in [50, 100, 150, 180]:
            #     selected_power = dict()
            #     ls = list()
            #     selected_flag = pd.DataFrame(np.zeros([48, df_pro.shape[1]]), index=np.arange(48), columns=df_pro.columns)
            #     for t in np.arange(48):
            #         selected_power[t] = pd.Series(np.zeros(df_sum_area.shape[0]))
            #         chosen_id = np.random.randint(0, df_pro.columns.shape[0], the_num_of_choose)
            #         chosen_sto = df_pro.columns.to_numpy()[chosen_id]
            #         for col in chosen_sto:
            #             selected_power[t] += dc[col][t]
            #     selected_power_pd = pd.DataFrame(selected_power)
            #     selected_power_flatten = pd.DataFrame(selected_power_pd.to_numpy().flatten(), columns=['power'])
            #
            #     # sns_plot
            #     try:
            #         os.makedirs('./stochastic_chosen/{0}_{1}_aggregated/sns_plot'
            #                     .format(months[num_mon], city[num_city]))
            #     except OSError:
            #         pass
            #     selected_power_flatten['timepoint'] = list(np.arange(selected_power_pd.shape[1])) * \
            #                                           selected_power_pd.shape[0]
            #     fig, ax = plt.subplots()
            #     ax = sns.lineplot(x='timepoint', y='power', data=selected_power_flatten)
            #     plt.title('the_aggregated_with_the_num_{2}_in_{0}'
            #             .format(months[num_mon], city[num_city], the_num_of_choose))
            #     plt.grid()
            #     plt.xlabel('time points')
            #     plt.ylabel('Power/kW')
            #     plt.xlim((0, 48))
            #     plt.ylim((0, 500))
            #     plt.savefig('./stochastic_chosen/{0}_{1}_aggregated/sns_plot/the_aggregated_with_the_num_as_{2}.png'.
            #                 format(months[num_mon], city[num_city], the_num_of_choose))
            #     plt.close()
            #
            #     # box_plot
            #     try:
            #         os.makedirs('./stochastic_chosen/{0}_{1}_aggregated/box_plot'
            #                     .format(months[num_mon], city[num_city]))
            #     except OSError:
            #         pass
            #     fig, ax = plt.subplots(1, 1)
            #     selected_power_pd.boxplot(column=list(np.arange(48)))
            #     plt.ylim((0, 800))
            #     plt.xlabel('time points')
            #     plt.ylabel('Power/kW')
            #     plt.title('the stochastic aggregated with the num of user as {}'.format(the_num_of_choose))
            #     plt.savefig(
            #         './stochastic_chosen/{0}_{1}_aggregated/box_plot/the_aggregated_with_critic_as_{2}.png'
            #         .format(months[num_mon], city[num_city], the_num_of_choose))
            #     plt.close()
            #
            #     # all month plot
            #     try:
            #         os.makedirs('./stochastic_chosen/{0}_{1}_aggregated/day_plot'
            #                     .format(months[num_mon], city[num_city]))
            #     except OSError:
            #         pass
            #     # plot the month aggregated performance
            #     selected_power_np = selected_power_pd.to_numpy()
            #     fig, ax = plt.subplots()
            #     for day in range(selected_power_np.shape[0]):
            #         ax.plot(selected_power_np[day])
            #     ax.set_ylim((0, 800))
            #     plt.grid()
            #     plt.xlabel('time points')
            #     plt.ylabel('Power/kW')
            #     plt.title('Aggregated_whole_month_with_critic_{2}_in_{0}'
            #               .format(months[num_mon], city[num_city], the_num_of_choose))
            #     plt.savefig('./stochastic_chosen/{0}_{1}_aggregated/day_plot/the_whole_month_with_critic_as_{2}.png'
            #                 .format(months[num_mon], city[num_city], the_num_of_choose))
            #     plt.close()

        #         try:
    #             os.makedirs('./aggregated_image/{}_{}_aggregated/scatter_plot'
    #             .format(months[num_mon], city[num_city]))
    #         except OSError:
    #             pass
    #         # scatter plot the aggregated performance
    #         fig, ax = plt.subplots(1, 1)
    #         selected_power_96 = selected_power_pd.to_numpy().reshape((-1, 2, 48))
    #         selected_power_96 = np.swapaxes(selected_power_96, 1, 2).reshape((-1, 96))
    #         for j in range(selected_power_96.shape[0]):
    #             plt.scatter(np.arange(96), selected_power_96[j, :], c='k', alpha=0.3, s=16)
    #         plt.xlabel('time points')
    #         plt.ylabel('Power/kW')
    #         plt.title('the aggregated performance in scattered plot with critic as {}'.format(critic))
    #         plt.savefig('./aggregated_image/{}_{}_aggregated/scatter_plot/the_aggregated_with_critic_as_{}.png'.
    #                     format(months[num_mon], city[num_city], critic))
    #         plt.close()
    #
    #         # plot the error area figure
    #         try:
    #             os.makedirs('./aggregated_image/{}_{}_aggregated/sns_plot'.format(months[num_mon], city[num_city]))
    #         except OSError:
    #             pass
    #         selected_power_flatten_pd = pd.DataFrame(selected_power_96.flatten())
    #         selected_power_flatten_pd.rename(columns={0: 'power'}, inplace=True)
    #         selected_power_flatten_pd['hour'] = list(np.arange(96)) * selected_power_96.shape[0]
    #         fig, ax = plt.subplots(1, 1)
    #         sns.relplot(x='hour', y='power', kind='line', data=selected_power_flatten_pd)
    #         plt.title('the aggregated performance in error area plot with critic as {}'.format(critic))
    #         plt.savefig('./aggregated_image/{}_{}_aggregated/sns_plot/the_aggregated_with_critic_as_{}.png'.
    #                     format(months[num_mon], city[num_city], critic))
    #         plt.close()
    #
    #     print('the num of month is {}'.format(months[num_mon]))
    # # --------------------------------------------------------------------------
    # # show the user's uncertainty changing during the day and the season
    # # --------------------------------------------------------------------------
    #     dc = dict()
    #     dc_qu = dict()
    #     dc_len = dict()
    #     fig, ax = plt.subplots(1, 1)
    #     for col in df_pro.columns[0:20]:
    #         df_user = df_pro[col].to_numpy().reshape((-1, 96))
    #         df_user_pd = pd.DataFrame(df_user, columns=np.arange(96))
    #         df_user_pd_qu = df_user_pd.quantile([0.25, 0.5, 0.75])
    #         df_user_pd_qu = df_user_pd_qu.T
    #         df_user_pd_qu['length'] = df_user_pd_qu[0.75] - df_user_pd_qu[0.25]
    #         dc[col] = df_user_pd
    #         dc_qu[col] = df_user_pd_qu
    #         dc_len[col] = df_user_pd_qu['length']
    #         ax.plot(df_user_pd_qu['length'], label=col)
    #     plt.show()
    #     plt.close()
    # --------------------------------------------------------------------------
    # discuss the time resolution for the aggregated performance
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # discuss the number of users and the aggregated performance
    # --------------------------------------------------------------------------

    # ---------------------------------------------------------------------------
    # discuss the satisfied performance
    # discuss the aggregated performance
    # --------------------------------------------------------------------------
