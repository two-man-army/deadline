use std::io;

fn main() {
    let mut input = String::new();
    let stdin = std::io::stdin();
    stdin.read_line(&mut input);
    let numbers: Vec<f64> = input.trim().split(", ").map(|x| x.parse::<f64>().unwrap()).collect();
    let sum: f64 = numbers.iter().sum();
    println!("{:?}", sum);
}
