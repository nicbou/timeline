export function formattedAmount(amount){
    let formattedAmount = (Math.round(Math.round(Number(amount)) * 100) / 100).toLocaleString('en-GB');
    if(formattedAmount === '-0.00'){
      formattedAmount = '0.00';
    }
    else if(formattedAmount === '-0'){
      formattedAmount = '0';
    }
    return `${formattedAmount} €`.replace('-', '−');
}