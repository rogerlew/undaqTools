import unittest
import numpy as np
from numpy.testing import assert_array_almost_equal
import matplotlib.pyplot as plt
        
from undaqTools.steeringentropy import SteeringEntropyModel
from undaqTools.misc.cdf import CDF, percentile

testdata = './data/uniformtestdata' # space delimited ASCII of 10,000 random digits
                               # from uniform distribution between -270 and 270

sintestdata = './data/sintestdata'

realwheeldata = './data/realwheeldata'

class Test_build_lpfilter(unittest.TestCase):
    def test0(self):
        se_model = SteeringEntropyModel()
        b,a = se_model._build_lpfilter(60)

        rb = np.array([-0.13360409+0.j])
        ra = np.array([ 1.00000000 +0.00000000e+00j,
                       -2.16362300 +0.00000000e+00j,
                        2.34063224 +0.00000000e+00j,
                       -1.56493800 +0.00000000e+00j,
                        0.64665620 -1.33112026e-16j,
                       -0.13360409 +2.22495512e-17j])
                   
        assert_array_almost_equal(rb, b)
        assert_array_almost_equal(ra, a)
    
class Test_resample(unittest.TestCase):
    def setUp(self):
        global realwheeldata
        with open(realwheeldata,'rb') as f:
            self.data = map(float, f.read().split())

    def test0(self):
        u = self.data
        se_model = SteeringEntropyModel()
        x = se_model._resample(u[-60*60:], 60)

        r = \
     np.array([ -1.61215419e-12,  -2.40321754e-04,  -2.33080451e-02,
                -9.04642339e-02,   1.40190084e-01,   3.74297171e-01,
                 3.12934111e-01,   4.95131080e-01,   1.14154168e+00,
                 4.42629737e+00,   7.19004268e+00,   5.76661990e+00,
                 1.37710045e+00,  -4.04657820e+00,  -4.46455455e+00,
                -2.74182091e+00,  -2.60887713e+00,  -1.81214933e+00,
                -2.29040129e+00,  -2.09464324e+00,  -6.74396456e-01,
                 3.12771720e+00,   6.63539749e+00,   6.68099218e+00,
                 5.23367001e+00,   1.06144188e+00,  -2.78478967e+00,
                -2.85377674e+00,  -2.78654061e+00,  -1.83510684e+00,
                -1.81865681e+00,  -2.16201553e+00,  -1.47048413e+00,
                -5.93937038e-01,  -2.46527449e-01,  -7.68822860e-01,
                -5.15642230e-01,  -6.20144084e-01,  -9.12087358e-01,
                -8.25760725e-01,  -7.28395225e-01,  -7.20917093e-01,
                -7.78745685e-01,  -6.08390133e-01,  -4.78147581e-01,
                -4.49870745e-01,  -5.39254885e-01,  -4.69299635e-01,
                -4.69071835e-01,  -4.40025322e-01,   1.40124371e-01,
                 2.70363641e+00,   5.00318748e+00,   4.00632747e+00,
                 2.51918500e+00,   9.22983233e-01,   1.43594568e+00,
                 2.25647645e+00,   1.80745664e+00,   1.75190705e+00,
                 2.34702181e-01,  -1.97572019e+00,  -2.37761044e+00,
                -2.30117739e+00,  -2.24715329e+00,  -1.93689929e+00,
                -1.88823604e+00,  -1.50879687e+00,  -7.65443800e-01,
                -4.14108223e-01,  -3.73872068e-01,   5.63886810e-02,
                 1.95715259e+00,   4.03690003e+00,   2.98087218e+00,
                -6.10729709e-01,  -1.55756097e+00,  -2.60003697e-01,
                 1.62767474e+00,   3.71047087e+00,   1.09611045e+00,
                 9.53114039e-01,   1.72472163e+00,   6.53023245e-01,
                -1.02539482e-01,  -2.11323519e+00,  -1.85226015e+00,
                -1.74608508e+00,  -1.91669067e+00,  -1.04470412e+00,
                -7.69943802e-01,  -1.69874535e-01,  -1.40893297e-01,
                -2.10597725e-01,  -2.52120916e-02,  -1.41044777e-01,
                 4.56470110e-01,   2.17295580e+00,   4.19018796e+00,
                 3.55326774e+00,   6.20266710e-01,  -1.11846410e+00,
                -5.01573652e-01,  -3.42985356e-01,  -2.94555007e-01,
                -8.08163367e-02,  -3.76477302e-01,  -1.50299007e+00,
                -2.99860099e+00,  -2.55552203e+00,  -2.27317862e+00,
                -2.17586942e+00,  -1.97183132e+00,  -2.02211316e+00,
                -1.40599577e+00,  -5.74288496e-01,   1.15984166e+00,
                 4.23182774e+00,   4.75834404e+00,   3.74200684e+00,
                 3.13959278e+00,   1.28464022e+00,  -1.63338185e-01,
                -4.59846989e-01,  -3.87030930e-02,  -1.47890773e-01,
                -7.81543211e-02,   7.04473154e-02,  -2.85587300e-01,
                -4.98040519e-01,  -5.05362319e-01,  -2.10988255e-01,
                -2.96243919e-01,  -3.08167185e-01,  -2.28173481e-01,
                -3.39205789e-01,  -2.17406734e-01,  -3.07119992e-01,
                -2.80856318e-01,  -2.01187240e-01,  -9.08931618e-02,
                 1.19209975e-04,  -1.03781679e-01,   1.68491206e-01,
                 4.01036790e-01,   2.91845195e-01,   6.72996081e-02,
                -3.33300925e-02,   1.26432268e-01,   8.32852023e-01,
                 1.88439781e+00,   1.33883460e+00,   4.80435455e-01,
                -2.43751156e-01,  -4.57317651e-01,  -5.00984921e-01,
                -7.37219937e-01,  -9.84904261e-01,  -1.31724659e+00,
                -1.03104538e+00,  -8.23229571e-01,  -4.19957897e-01,
                -2.62460181e-01,   1.20635374e+00,   4.33611445e+00,
                 4.18854222e+00,   2.14247691e+00,  -2.11679116e-01,
                -5.72818587e-01,   7.55383702e-01,   1.57580810e+00,
                 2.16247799e+00,   1.70824825e+00,   1.98917050e+00,
                 1.96270109e+00,   1.28671320e+00,  -1.08375824e-01,
                -1.05344979e+00,  -1.81169560e+00,  -2.51135819e+00,
                -1.76963679e+00,  -1.80747840e+00,  -1.19208123e+00,
                -1.01487994e+00,  -9.33388519e-01,  -3.51813158e-01,
                -7.32129130e-01,  -4.02376988e-01,  -4.07198280e-01,
                -5.57795939e-01,  -9.71627735e-01,  -1.77767380e+00,
                -1.62379647e+00,  -1.70260138e+00,  -1.73850730e+00,
                -1.63276843e+00,  -1.74199713e+00,  -1.68546087e+00,
                -1.61694517e+00,  -1.55739340e+00,  -1.50227678e+00,
                -1.58767956e+00,  -1.65341566e+00,  -1.56110869e+00,
                -1.69875060e+00,  -1.70323970e+00,  -1.65476178e+00,
                -1.76280986e+00,  -1.55644944e+00,  -1.48442341e+00,
                -1.66990811e+00,  -1.69235942e+00,  -1.69908318e+00,
                -1.62778083e+00,  -1.67340936e+00,  -1.64669665e+00,
                -1.58731759e+00,  -1.53574846e+00,  -1.64873524e+00,
                -2.25637968e+00,  -4.03930444e+00,  -5.10310300e+00,
                 3.74270189e-01,   4.87412168e+00,   3.09786073e+00,
                 3.63976627e+00,   3.53954132e+00,   3.06438935e+00,
                 3.55312209e+00,   3.24430576e+00,   3.68814282e+00,
                 3.61790133e+00,   3.66176895e+00,   3.67115383e+00,
                 3.51618968e+00,   3.68577762e+00,   3.69906184e+00,
                 4.05961352e+00,   4.07009574e+00,   3.95738239e+00])
                   
        assert_array_almost_equal(r,x)
        
class Test_fit_baseline(unittest.TestCase):
    def setUp(self):
        global testdata
        with open(testdata,'rb') as f:
            self.data = map(float, f.read().split())

    def test_fit_baseline_alpha_adj(self):
        u = self.data
        se_model = SteeringEntropyModel(alpha=0.05)
        hbas = se_model.fit_baseline(u[:2*60*60])

        self.assertAlmostEqual(hbas, 1.6410033779603466)

    def test_fit_baseline_coeffs(self):
        u = self.data
        se_model = SteeringEntropyModel()
        se_model.fit_baseline(u[:2*60*60])

        r = np.array([ 1.        , -0.34963801,  0.20299164, -0.20005458])
        assert_array_almost_equal(se_model.b_pe, r)

    def test_fit_baseline_hbas(self):
        u = self.data
        se_model = SteeringEntropyModel()
        hbas = se_model.fit_baseline(u[:2*60*60])

        self.assertAlmostEqual(hbas, 2.2739162914073892)
        
    def test_fit_baseline_m_adj(self):
        u = self.data
        se_model = SteeringEntropyModel(M=7)
        hbas = se_model.fit_baseline(u[:2*60*60])

        self.assertAlmostEqual(hbas, 2.2938478599767125)
        
        
    def test_fit_baseline_resamplefs_adj(self):
        u = self.data
        se_model = SteeringEntropyModel(resample_fs=5.)
        hbas = se_model.fit_baseline(u[:2*60*60])

        self.assertAlmostEqual(hbas, 2.492228125216982)
                     
class Test_get_entropy(unittest.TestCase):
    def setUp(self):
        global testdata
        with open(testdata,'rb') as f:
            self.data = map(float, f.read().split())

    def test_get_entropy(self):
        u = self.data
        se_model = SteeringEntropyModel()
        hbas = se_model.fit_baseline(u[:2*60*60])
        h = se_model.get_entropy(u[-60*60:])

        self.assertAlmostEqual(h, 2.3165502390766974) 

    def test_get_entropy_empty_list(self):
        u = self.data
        se_model = SteeringEntropyModel()
        hbas = se_model.fit_baseline(u[:2*60*60])
        h = se_model.get_entropy([])

        self.assertAlmostEqual(h, 0.)

    def test_called_without_fit(self):
        u = self.data
        
        se_model = SteeringEntropyModel()
        with self.assertRaises(Exception):
            se_model.get_entropy()

class Test_sintestdata(unittest.TestCase):
    def setUp(self):
        global testdata
        with open(testdata,'rb') as f:
            self.data = map(float, f.read().split())

    def test_get_10pctlargeincrease(self):
        u = self.data
        se_model = SteeringEntropyModel()
        hbas = se_model.fit_baseline(u[:2*60*60])
        h = se_model.get_entropy(u[-60*60:])

        self.assertAlmostEqual(hbas, 2.2739162914073892)
        self.assertAlmostEqual(h, 2.3165502390766974)

class Test_plots(unittest.TestCase):
    def setUp(self):
        global realwheeldata
        with open(realwheeldata,'rb') as f:
            self.data = map(float, f.read().split())

    def test_lpfilter(self):
        u = self.data[-2*60*60:]
        se_model = SteeringEntropyModel()
        fig = se_model._lpfilter_bode()
        fig.savefig('./output/lpfilter.png')
        plt.close('all')

    def test_bode(self):
        u = self.data[-2*60*60:]
        se_model = SteeringEntropyModel()
        hbas = se_model.fit_baseline(u[:2*60*60])
        fig = se_model.bode()
        fig.savefig('./output/bode.png')
        plt.close('all')

    def test_baseline_tsplot(self):
        u = self.data[-2*60*60:]
        se_model = SteeringEntropyModel()
        h,fig = se_model.fit_baseline(u, _tsplot=True)
        fig.savefig('./output/baseline_ts.png', dpi=300)
        plt.close('all')

    def test_pedistplot0(self):
        u = self.data[-2*60*60:]
        se_model = SteeringEntropyModel()
        hbas = se_model.fit_baseline(u[:2*60*60])
        h, fig = se_model.get_entropy(u[60*60:2*60*60], _pedistplot=True)
        fig.savefig('./output/pedist_null.png', dpi=300)
        plt.close('all')
        
    def test_pedistplot(self):
        u = self.data[-2*60*60:]
        se_model = SteeringEntropyModel()
        hbas = se_model.fit_baseline(u[:2*60*60])
        h, fig = se_model.get_entropy(u[-60*60:], _pedistplot=True)
        fig.savefig('./output/pedist.png', dpi=300)
        plt.close('all')
        
    def test_pecdf(self):
        u = self.data[-2*60*60:]
        se_model = SteeringEntropyModel()
        hbas = se_model.fit_baseline(u[:2*60*60])
        fig = se_model.cdf.plot()
        fig.savefig('./output/pe_cdf.png')
        plt.close('all')

class Test_repr(unittest.TestCase):
    def setUp(self):
        global testdata
        with open(testdata,'rb') as f:
            self.data = map(float, f.read().split())
        
    def test_repr_nofit(self):
        se_model = SteeringEntropyModel()
        self.assertEqual(repr(se_model),
                         repr(eval(repr(se_model))))
        
    def test_repr_fit(self):
        u = self.data
        se_model = SteeringEntropyModel()
        se_model.fit_baseline(u[:2*60*60])

        se_model2 = eval(repr(se_model))

        self.assertAlmostEqual(se_model.resample_fs, se_model2.resample_fs)
        self.assertAlmostEqual(se_model.alpha, se_model2.alpha)
        self.assertAlmostEqual(se_model.M, se_model2.M)
        assert_array_almost_equal(se_model.b_pe, se_model2.b_pe)
        assert_array_almost_equal(se_model.pkbas, se_model2.pkbas)
        assert_array_almost_equal(se_model.bin_edges,
                                             se_model2.bin_edges)
        self.assertAlmostEqual(se_model.hbas, se_model2.hbas)
        self.assertEqual(repr(se_model.cdf), repr(se_model2.cdf))
                         
def suite():
    return unittest.TestSuite((
            unittest.makeSuite(Test_build_lpfilter),
            unittest.makeSuite(Test_resample),
            unittest.makeSuite(Test_fit_baseline),
            unittest.makeSuite(Test_get_entropy),
            unittest.makeSuite(Test_sintestdata),
            unittest.makeSuite(Test_plots),
            unittest.makeSuite(Test_repr)
                              ))

if __name__ == "__main__":
        
    # run tests
    runner = unittest.TextTestRunner()
    runner.run(suite())
